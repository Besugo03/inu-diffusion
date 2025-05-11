import numpy as np
import pickle
import os
from sklearn.preprocessing import LabelEncoder
# from sklearn.model_selection import train_test_split # Not explicitly used here but good for robust eval
import tensorflow as tf
from sentence_transformers import SentenceTransformer
import fasttext
# import fasttext.util # Only if you want to try auto-downloading FastText models

import gelbooru as gb

# --- Keras specific imports from tf.keras ---
Sequential = tf.keras.models.Sequential
Dense = tf.keras.layers.Dense
Dropout = tf.keras.layers.Dropout
to_categorical = tf.keras.utils.to_categorical
EarlyStopping = tf.keras.callbacks.EarlyStopping
load_model = tf.keras.models.load_model
Adam = tf.keras.optimizers.Adam

# --- Configuration ---
EMBEDDER_TYPE = "SBERT"  # Options: "SBERT" or "FASTTEXT"

# SBERT Config
SBERT_MODEL_NAME = 'all-MiniLM-L6-v2'

# FastText Config
# IMPORTANT: Download 'crawl-300d-2M-subword.bin' (or other .bin) manually from
# https://fasttext.cc/docs/en/crawl-vectors.html and place it in your project directory
# or provide the full path.
FASTTEXT_MODEL_PATH = 'crawl-300d-2M-subword.bin' # ~6.7GB
# FASTTEXT_MODEL_PATH = 'wiki.en.bin' # Smaller alternative, also download manually

# Shared Config
MODEL_DIR = "trained_models" # Directory to save models
LABEL_ENCODER_FILENAME = "tag_label_encoder.pkl"
# Keras model filename will include embedder type
KERAS_MODEL_FILENAME_TEMPLATE = "tag_classifier_{embedder_type}.h5"


CONFIDENCE_THRESHOLD_FOR_FEEDBACK = 0.85 # Adjusted
CONFIDENCE_TOP_PREDICTION_GATE_THRESHOLD = 0.85 # If top prediction is below this, ask for help
CONFIDENCE_MARGIN_GATE_THRESHOLD = 0.15      # If (Prob_Top1 - Prob_Top2) is less than this, ask for help
MIN_SAMPLES_FOR_TRAINING = 20
RETRAIN_EVERY_N_FEEDBACKS = 5
CATEGORIES = ["POSE_COMPOSITION", "CHARACTER_FEATURE", "ACCESSORY", "COLOR_MODIFIED", "OTHER_BAD"]

# --- Global State ---
embedder_model = None # Will hold SBERT or FastText model
current_embedding_dim = 0
label_encoder = None
classifier_model = None # Keras model
training_data = []    # List of tuples: (tag_string, category_string) - for persistent storage
feedback_buffer = []  # List of tuples: (tag_string, category_string) - for current session's retraining

# --- Heuristic Seed Data (Replace with your comprehensive lists!) ---
MY_POSE_COMPOSITION_WHITELIST = {"standing", "sitting", "full_body", "simple_background", "looking_at_viewer", "upper_body", "from_behind", "dynamic_angle", "white_background", "solo", "1girl", "profile", "cowboy_shot", "wide_shot"}
MY_BODY_FEATURES_SET = {"long_hair", "ahoge", "cat_ears", "breasts", "twin_tails", "short_hair", "ponytail", "elf_ears", "horns", "tail"}
MY_ACCESSORY_SET = {"glasses", "sword", "hat", "shirt", "ribbon", "necklace", "armor", "gun", "shield", "cape", "mask"}
MY_ATTIRE_SET = {"dress", "skirt", "pants", "sweater", "jacket", "socks", "stockings", "bikini", "swimsuit", "t-shirt", "hoodie", "overalls","panties","gloves", "boots", "school_uniform", "thighhighs"}
MY_COLOR_MODIFIED_PATTERNS_BASE = {"eyes", "hair", "dress", "skin", "shirt", "jacket", "background", "scarf", "ribbon"}
MY_COLORS = {"blue", "red", "green", "black", "white", "yellow", "purple", "pink", "orange", "brown", "blonde", "silver", "gold"}
MY_OTHER_BAD_SET = {"loli", "artist_signature", "censored", "text", "watermark", "bar_censor", "comic"}


# --- Utility and Core Functions ---

def get_user_feedback(tag_string, predicted_category, confidence):
    """Handles prompting the user for feedback."""
    print(f"  Tag: '{tag_string}' -> Predicted: '{predicted_category}' (Confidence: {confidence:.2f})")
    if predicted_category == "NEEDS_TRAINING" or confidence < CONFIDENCE_THRESHOLD_FOR_FEEDBACK:
        print(f"  Low confidence or needs training. Requesting feedback for '{tag_string}'.")
        print(f"  Available categories:")
        current_categories = label_encoder.classes_ if label_encoder else CATEGORIES
        for idx, cat_name in enumerate(current_categories):
            print(f"    {idx}: {cat_name}")
        
        while True:
            try:
                user_input_idx_str = input(f"  Enter correct category index for '{tag_string}' (or 's' to skip, 'p' to pass as predicted): ")
                if user_input_idx_str.lower() == 's':
                    print("  Skipped feedback, tag will not be used for training this round.")
                    return None # Indicate skipped
                if user_input_idx_str.lower() == 'p':
                    print(f"  Passing tag as predicted: {predicted_category}")
                    return predicted_category # Keep original prediction
                
                correct_category_idx = int(user_input_idx_str)
                correct_category_input = current_categories[correct_category_idx]
                print(f"  User feedback: '{tag_string}' is '{correct_category_input}'.")
                return correct_category_input
            except (ValueError, IndexError):
                print("  Invalid input. Please enter a valid number from the list, 's', or 'p'.")
    else: # Confident prediction
        print(f"  Confident prediction for '{tag_string}'.")
        return predicted_category


def get_embedding(tag_string):
    global embedder_model, EMBEDDER_TYPE
    if embedder_model is None:
        raise ValueError("Embedder model not initialized.")
    
    if EMBEDDER_TYPE == "SBERT":
        return embedder_model.encode([tag_string], show_progress_bar=False)[0]
    elif EMBEDDER_TYPE == "FASTTEXT":
        processed_tag = tag_string.lower().replace('_', ' ')
        return embedder_model.get_sentence_vector(processed_tag)
    else:
        raise ValueError(f"Unknown EMBEDDER_TYPE: {EMBEDDER_TYPE}")


def initialize_components():
    global embedder_model, current_embedding_dim, label_encoder, classifier_model, training_data, EMBEDDER_TYPE

    os.makedirs(MODEL_DIR, exist_ok=True)
    label_encoder_path = os.path.join(MODEL_DIR, LABEL_ENCODER_FILENAME)
    keras_model_filename = KERAS_MODEL_FILENAME_TEMPLATE.format(embedder_type=EMBEDDER_TYPE.lower())
    keras_model_path = os.path.join(MODEL_DIR, keras_model_filename)

    print(f"Initializing components with EMBEDDER_TYPE: {EMBEDDER_TYPE}")

    # 1. Initialize Embedder
    if EMBEDDER_TYPE == "SBERT":
        print(f"Loading SBERT model: {SBERT_MODEL_NAME}")
        embedder_model = SentenceTransformer(SBERT_MODEL_NAME)
        current_embedding_dim = embedder_model.get_sentence_embedding_dimension()
    elif EMBEDDER_TYPE == "FASTTEXT":
        if not os.path.exists(FASTTEXT_MODEL_PATH):
            print(f"ERROR: FastText model file not found: {FASTTEXT_MODEL_PATH}")
            print("Please download it from https://fasttext.cc/docs/en/crawl-vectors.html (e.g., crawl-300d-2M-subword.bin)")
            raise SystemExit("FastText model file missing.")
        print(f"Loading FastText model from {FASTTEXT_MODEL_PATH}...")
        embedder_model = fasttext.load_model(FASTTEXT_MODEL_PATH)
        current_embedding_dim = embedder_model.get_dimension()
    else:
        raise ValueError(f"Unknown EMBEDDER_TYPE: {EMBEDDER_TYPE}")
    print(f"{EMBEDDER_TYPE} model loaded. Embedding dimension: {current_embedding_dim}")

    # 2. Initialize LabelEncoder
    try:
        with open(label_encoder_path, 'rb') as f:
            label_encoder = pickle.load(f)
        print(f"Loaded LabelEncoder. Classes: {label_encoder.classes_}")
        # Ensure CATEGORIES are consistent with loaded encoder
        if not all(cat in label_encoder.classes_ for cat in CATEGORIES) or \
           not all(lc_cat in CATEGORIES for lc_cat in label_encoder.classes_):
            print("Warning: Predefined CATEGORIES mismatch loaded LabelEncoder. Re-fitting.")
            label_encoder.fit(list(set(list(label_encoder.classes_) + CATEGORIES))) # Merge and refit
            with open(label_encoder_path, 'wb') as f: pickle.dump(label_encoder, f)

    except FileNotFoundError:
        print("LabelEncoder not found. Initializing new one.")
        label_encoder = LabelEncoder()
        label_encoder.fit(CATEGORIES)
        with open(label_encoder_path, 'wb') as f: pickle.dump(label_encoder, f)

    # 3. Initialize Keras Classifier Model
    try:
        classifier_model = load_model(keras_model_path)
        print(f"Loaded existing Keras classifier model from {keras_model_path}")
        if classifier_model.input_shape[1] != current_embedding_dim:
            print(f"Warning: Loaded Keras model input dim ({classifier_model.input_shape[1]}) "
                  f"does not match current {EMBEDDER_TYPE} embedding dim ({current_embedding_dim}). "
                  "Model will be rebuilt on next training.")
            classifier_model = None
    except Exception as e: # Broad exception for file not found, HDF5 issues, etc.
        print(f"Keras classifier model from {keras_model_path} not found or error loading ({e}). "
              "Will be created on first effective training.")
        classifier_model = None

    # 4. Load persistent training_data (e.g., from a CSV or pickle)
    # For this example, we rely on the global 'training_data' being seeded or empty
    # In a real app, you'd load it here:
    # try:
    #     with open(os.path.join(MODEL_DIR, "all_training_data.pkl"), 'rb') as f:
    #         training_data = pickle.load(f)
    #     print(f"Loaded {len(training_data)} samples from persistent storage.")
    # except FileNotFoundError:
    #     print("No persistent training_data found.")
    #     training_data = []
    print(f"Current in-memory training_data size (from seed or previous runs if not persistent): {len(training_data)}")


def build_classifier_model_keras(input_dim_keras): # Renamed for clarity
    model = Sequential([
        Dense(128, activation='relu', input_shape=(input_dim_keras,)),
        Dropout(0.4),
        Dense(64, activation='relu'),
        Dropout(0.4),
        Dense(len(label_encoder.classes_), activation='softmax')
    ])
    model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
    return model

def train_or_finetune_classifier(force_retrain_all_from_training_data=False):
    global classifier_model, training_data, feedback_buffer, current_embedding_dim

    keras_model_filename = KERAS_MODEL_FILENAME_TEMPLATE.format(embedder_type=EMBEDDER_TYPE.lower())
    keras_model_path = os.path.join(MODEL_DIR, keras_model_filename)

    data_for_current_training_session = []
    
    if force_retrain_all_from_training_data:
        if not training_data:
            print("Force retrain requested, but no persistent training_data available.")
            return
        print(f"Force retraining on all {len(training_data)} samples from persistent training_data.")
        data_for_current_training_session.extend(training_data)
        # Also include any new feedback from the current session
        if feedback_buffer:
             print(f"Adding {len(feedback_buffer)} new feedback samples to this full retrain.")
             new_feedback_not_in_training_data = [fb for fb in feedback_buffer if fb not in training_data] # Avoid duplicates if any
             data_for_current_training_session.extend(new_feedback_not_in_training_data)
             training_data.extend(new_feedback_not_in_training_data) # Persist new feedback
             feedback_buffer.clear()

    elif feedback_buffer:
        print(f"Fine-tuning on {len(feedback_buffer)} new feedback samples.")
        data_for_current_training_session.extend(feedback_buffer)
        training_data.extend(feedback_buffer) # Persist new feedback
        feedback_buffer.clear()
    else:
        print("No new feedback and not forcing full retrain. Skipping training.")
        return

    if not data_for_current_training_session:
        print("No data selected for this training session.")
        return
    
    # Ensure enough total samples exist in training_data before attempting any training
    if len(training_data) < MIN_SAMPLES_FOR_TRAINING:
        print(f"Need at least {MIN_SAMPLES_FOR_TRAINING} total samples in training_data for training. Current: {len(training_data)}. "
              "Collect more feedback.")
        # Put data back into feedback_buffer if it was cleared
        feedback_buffer.extend(data_for_current_training_session)
        # Remove from training_data if it was just added
        for item in data_for_current_training_session:
            if item in training_data: training_data.remove(item)
        return

    print(f"Preparing to train/fine-tune Keras model on {len(data_for_current_training_session)} samples.")
    tags = [item[0] for item in data_for_current_training_session]
    labels_str = [item[1] for item in data_for_current_training_session]

    print(f"Encoding {len(tags)} tags with {EMBEDDER_TYPE}...")
    tag_embeddings = np.array([get_embedding(tag) for tag in tags])
    
    # Ensure label_encoder handles all labels
    all_current_labels_in_batch = list(set(labels_str))
    all_known_labels = list(set(all_current_labels_in_batch) | set(label_encoder.classes_))
    if len(all_known_labels) > len(label_encoder.classes_): # New category encountered
        print(f"New labels detected in batch. Re-fitting LabelEncoder. Old: {label_encoder.classes_}, New from batch: {all_current_labels_in_batch}")
        label_encoder.fit(all_known_labels) # Fit on the union
        with open(os.path.join(MODEL_DIR, LABEL_ENCODER_FILENAME), 'wb') as f: pickle.dump(label_encoder, f)
        if classifier_model and classifier_model.layers[-1].output_shape[-1] != len(label_encoder.classes_):
            print("LabelEncoder classes changed, Keras model output layer is incompatible. Rebuilding model.")
            classifier_model = None # Force rebuild

    labels_encoded = label_encoder.transform(labels_str)
    labels_one_hot = to_categorical(labels_encoded, num_classes=len(label_encoder.classes_))

    if classifier_model is None or classifier_model.input_shape[1] != current_embedding_dim:
        if classifier_model is not None and classifier_model.input_shape[1] != current_embedding_dim:
            print(f"Keras model input dim ({classifier_model.input_shape[1]}) mismatches current embedder dim ({current_embedding_dim}). Rebuilding.")
        else:
            print("Building new Keras classifier model.")
        classifier_model = build_classifier_model_keras(current_embedding_dim)
    
    is_initial_full_train = force_retrain_all_from_training_data or \
                            (len(training_data) - len(data_for_current_training_session) < MIN_SAMPLES_FOR_TRAINING) # Heuristic for first substantial train

    epochs_to_run = 30 if is_initial_full_train else 10 # More for full, fewer for fine-tune
    batch_s = 16 if is_initial_full_train else 8
    patience_es = 7 if is_initial_full_train else 3


    print(f"Training Keras model with {epochs_to_run} epochs, batch size {batch_s}...")
    history = classifier_model.fit(
        tag_embeddings, labels_one_hot,
        epochs=epochs_to_run,
        batch_size=batch_s,
        verbose=1,
        validation_split=0.15 if len(data_for_current_training_session) >= 20 else None,
        callbacks=[EarlyStopping(monitor='val_loss', patience=patience_es, restore_best_weights=True)] if len(data_for_current_training_session) >= 20 else []
    )
    
    classifier_model.save(keras_model_path)
    print(f"Keras classifier model saved to {keras_model_path}")
    # Save all training_data persistently
    # with open(os.path.join(MODEL_DIR, "all_training_data.pkl"), 'wb') as f:
    #    pickle.dump(training_data, f)
    # print(f"Saved all {len(training_data)} training samples to persistent storage.")


def predict_tag(tag_string):
    if embedder_model is None or classifier_model is None or label_encoder is None:
        return "NEEDS_INITIALIZATION", 0.0
    
    try:
        tag_embedding = get_embedding(tag_string).reshape(1, -1)
        prediction_probs = classifier_model.predict(tag_embedding, verbose=0)[0]
        
        predicted_class_index = np.argmax(prediction_probs)
        confidence = float(prediction_probs[predicted_class_index])
        
        if predicted_class_index >= len(label_encoder.classes_):
             print(f"Warning: Predicted index {predicted_class_index} out of bounds for LabelEncoder classes ({len(label_encoder.classes_)}).")
             return "ERROR_CLASS_MISMATCH", 0.0

        predicted_category = label_encoder.inverse_transform([predicted_class_index])[0]
        return predicted_category, confidence
    except Exception as e: # Catch errors during prediction (e.g. model not fully trained)
        print(f"Error during prediction for '{tag_string}': {e}")
        if classifier_model is None: return "NEEDS_TRAINING", 0.0
        return "ERROR_PREDICTION", 0.0


def process_tag_and_collect_feedback(tag_string):
    global feedback_buffer
    
    predicted_category, confidence = predict_tag(tag_string)
    
    # Use the centralized feedback function
    corrected_category_or_signal = get_user_feedback(tag_string, predicted_category, confidence)

    if corrected_category_or_signal is not None: # Not skipped
        # Add to feedback buffer only if it's a genuine correction or a low-confidence item the user confirmed/changed
        # Or if it's a new tag the model hasn't seen and user provided input
        is_different_from_prediction = (predicted_category != corrected_category_or_signal)
        was_low_confidence = (confidence < CONFIDENCE_THRESHOLD_FOR_FEEDBACK or predicted_category == "NEEDS_TRAINING" or predicted_category == "NEEDS_INITIALIZATION")
        
        if is_different_from_prediction or was_low_confidence:
            feedback_buffer.append((tag_string, corrected_category_or_signal))
            print(f"  Added '{tag_string}':'{corrected_category_or_signal}' to feedback buffer (Size: {len(feedback_buffer)})")
        
        if len(feedback_buffer) >= RETRAIN_EVERY_N_FEEDBACKS:
            print(f"Reached {RETRAIN_EVERY_N_FEEDBACKS} feedbacks, triggering fine-tuning.")
            train_or_finetune_classifier()
        
        return corrected_category_or_signal
    
    return predicted_category # If skipped, return original prediction


def add_manual_correction(tag_string, correct_category_string):
    """
    Manually adds a tag and its correct category to the feedback buffer
    for the next retraining cycle. Also ensures it gets into persistent training_data.
    """
    global feedback_buffer, training_data, label_encoder

    if label_encoder is None:
        print("ERROR: LabelEncoder not initialized. Cannot add manual correction yet.")
        print("Please run initialize_components() first or ensure CATEGORIES are defined.")
        return

    if correct_category_string not in label_encoder.classes_:
        # Option 1: Add the new category if it's truly new and desired
        # print(f"Warning: '{correct_category_string}' is a new category. Adding to LabelEncoder.")
        # new_classes = list(label_encoder.classes_) + [correct_category_string]
        # label_encoder.fit(new_classes) # This would require model rebuild if output layer size changes
        # For simplicity now, we'll assume only existing categories are used for manual correction.
        # Option 2: Error out
        print(f"ERROR: Category '{correct_category_string}' is not in the known categories: {label_encoder.classes_}")
        print("Please use one of the existing categories or update CATEGORIES and re-initialize.")
        return

    correction = (tag_string.strip().lower().replace(" ", "_"), correct_category_string) # Normalize tag
    
    # Add to feedback buffer for immediate retraining consideration
    if correction not in feedback_buffer: # Avoid duplicates in current buffer
        feedback_buffer.append(correction)
        print(f"Added manual correction to feedback_buffer: {correction}")
    else:
        print(f"Manual correction {correction} already in feedback_buffer.")

    # Ensure it's also in the main training_data for long-term persistence
    # (train_or_finetune_classifier already adds from feedback_buffer to training_data)

    # Optional: Trigger immediate retraining if desired after a manual correction
    if len(feedback_buffer) >= 1: # Or some other condition
        print("Triggering retraining after manual correction.")
        train_or_finetune_classifier()

def predict_tag_with_confidence_scores(tag_string):
    """
    Predicts tag category and returns all class probabilities.
    This is needed for margin/entropy checks.
    """
    if embedder_model is None or classifier_model is None or label_encoder is None:
        # Return a structure indicating failure, with dummy probabilities
        return "NEEDS_INITIALIZATION", np.zeros(len(CATEGORIES) if not label_encoder else len(label_encoder.classes_))
    
    try:
        tag_embedding = get_embedding(tag_string).reshape(1, -1)
        # Ensure classifier_model is not None before predicting
        if classifier_model is None:
            return "NEEDS_TRAINING", np.zeros(len(label_encoder.classes_))

        all_prediction_probs = classifier_model.predict(tag_embedding, verbose=0)[0]
        
        predicted_class_index = np.argmax(all_prediction_probs)
        
        if predicted_class_index >= len(label_encoder.classes_):
             print(f"Warning: Predicted index {predicted_class_index} out of bounds for LabelEncoder classes ({len(label_encoder.classes_)}).")
             return "ERROR_CLASS_MISMATCH", np.zeros(len(label_encoder.classes_))

        predicted_category = label_encoder.inverse_transform([predicted_class_index])[0]
        return predicted_category, all_prediction_probs # Return all probabilities
        
    except Exception as e:
        print(f"Error during full prediction for '{tag_string}': {e}")
        if classifier_model is None: return "NEEDS_TRAINING", np.zeros(len(label_encoder.classes_))
        return "ERROR_PREDICTION", np.zeros(len(label_encoder.classes_))


def get_prediction_with_confidence_gate(tag_string, allow_interactive_feedback=True):
    """
    Gets a prediction. If confidence is too low based on gate thresholds,
    optionally requests user feedback, retrains, and then predicts again.
    """
    global feedback_buffer # To add feedback

    predicted_category, all_probs = predict_tag_with_confidence_scores(tag_string)
    
    if predicted_category in ["NEEDS_INITIALIZATION", "NEEDS_TRAINING", "ERROR_CLASS_MISMATCH", "ERROR_PREDICTION"]:
        print(f"  Initial prediction for '{tag_string}' failed or model not ready: {predicted_category}")
        if allow_interactive_feedback:
            # Directly ask for feedback as we have no good prediction
            print(f"  Requesting feedback for '{tag_string}' due to prediction issue.")
            corrected_category = get_user_feedback(tag_string, predicted_category, 0.0) # Pass 0.0 confidence
            if corrected_category is not None: # User provided feedback (not skipped)
                feedback_buffer.append((tag_string, corrected_category))
                print(f"  Added '{tag_string}':'{corrected_category}' to feedback buffer (Size: {len(feedback_buffer)})")
                if len(feedback_buffer) >= RETRAIN_EVERY_N_FEEDBACKS: # Check if retraining is due
                    print(f"  Confidence gate: Reached {RETRAIN_EVERY_N_FEEDBACKS} feedbacks, triggering fine-tuning.")
                    train_or_finetune_classifier()
                    # After retraining, predict again
                    print(f"  Confidence gate: Predicting again for '{tag_string}' after retraining.")
                    predicted_category, _ = predict_tag_with_confidence_scores(tag_string) # Use the new prediction
                    return predicted_category # Return the new top prediction
                return corrected_category # Return user's correction if no immediate retrain
            else: # User skipped
                return predicted_category # Return the original problematic state
        else: # Not allowing interactive feedback
            return predicted_category 

    # Normal prediction was made, now check confidence gates
    top_confidence = float(np.max(all_probs))
    
    # Sort probabilities to get top two for margin check
    sorted_probs = np.sort(all_probs)[::-1]
    margin = 0.0
    if len(sorted_probs) > 1:
        margin = float(sorted_probs[0] - sorted_probs[1])

    needs_feedback_due_to_gate = False
    if top_confidence < CONFIDENCE_TOP_PREDICTION_GATE_THRESHOLD:
        print(f"  Confidence gate: Top prediction confidence for '{tag_string}' ({top_confidence:.2f}) is below threshold ({CONFIDENCE_TOP_PREDICTION_GATE_THRESHOLD}).")
        needs_feedback_due_to_gate = True
    elif margin < CONFIDENCE_MARGIN_GATE_THRESHOLD and len(sorted_probs) > 1:
        print(f"  Confidence gate: Prediction margin for '{tag_string}' ({margin:.2f}) is below threshold ({CONFIDENCE_MARGIN_GATE_THRESHOLD}). Top two similar.")
        needs_feedback_due_to_gate = True

    if needs_feedback_due_to_gate and allow_interactive_feedback:
        print(f"  Requesting feedback for '{tag_string}' due to confidence gate.")
        # get_user_feedback will show the current top prediction
        corrected_category = get_user_feedback(tag_string, predicted_category, top_confidence) 
        
        if corrected_category is not None: # User provided feedback (not skipped)
            # Add to feedback buffer only if the user's label is different or if it was a gate trigger
            if predicted_category != corrected_category or needs_feedback_due_to_gate:
                 feedback_buffer.append((tag_string, corrected_category))
                 print(f"  Added '{tag_string}':'{corrected_category}' to feedback buffer (Size: {len(feedback_buffer)})")

            if len(feedback_buffer) >= RETRAIN_EVERY_N_FEEDBACKS: # Check if retraining is due
                print(f"  Confidence gate: Reached {RETRAIN_EVERY_N_FEEDBACKS} feedbacks, triggering fine-tuning.")
                train_or_finetune_classifier()
                # After retraining, predict again to give the "final" answer for this call
                print(f"  Confidence gate: Predicting again for '{tag_string}' after retraining.")
                final_predicted_category, _ = predict_tag_with_confidence_scores(tag_string)
                return final_predicted_category
            
            return corrected_category # Return the user's correction if no immediate retrain
        else: # User skipped feedback
            return predicted_category # Return the original uncertain prediction
    
    # If confidence is good, or no interactive feedback allowed
    return predicted_category

# --- Main Execution ---
if __name__ == '__main__':
    # --- Choose embedder type (user can change this) ---
    # EMBEDDER_TYPE = "SBERT" 
    EMBEDDER_TYPE = "FASTTEXT" # <<<<<<<<<< CHANGE THIS TO TEST DIFFERENT EMBEDDERS
    print(f"***** RUNNING WITH EMBEDDER: {EMBEDDER_TYPE} *****")

    # --- Populate initial training_data from heuristic lists (if training_data is empty) ---
    if not training_data: # Only seed if global training_data is currently empty
        initial_seed_data = []
        for t in MY_POSE_COMPOSITION_WHITELIST: initial_seed_data.append((t, "POSE_COMPOSITION"))
        for t in MY_BODY_FEATURES_SET: initial_seed_data.append((t, "CHARACTER_FEATURE"))
        for t in MY_ATTIRE_SET: initial_seed_data.append((t, "ATTIRE"))
        for t in MY_ACCESSORY_SET: initial_seed_data.append((t, "ACCESSORY"))
        for t_base in MY_COLOR_MODIFIED_PATTERNS_BASE:
            for color in MY_COLORS:
                initial_seed_data.append((f"{color}_{t_base}", "COLOR_MODIFIED"))
        for t in MY_OTHER_BAD_SET: initial_seed_data.append((t, "OTHER_BAD"))
        
        if initial_seed_data:
            print(f"Seeding global training_data with {len(initial_seed_data)} unique samples (multiplied for initial training).")
            # Add unique items first, then multiply for more training weight if desired, or just use unique
            unique_initial_seed_data = list(set(initial_seed_data)) # Get unique tuples
            training_data.extend(unique_initial_seed_data * 3) # Multiply unique items

    # --- Initialize all components based on EMBEDDER_TYPE ---
    initialize_components()
    
    # --- Initial Training (if no Keras model loaded and enough seed data) ---
    if classifier_model is None and len(training_data) >= MIN_SAMPLES_FOR_TRAINING:
        print("\nNo existing Keras model loaded for this embedder and enough seed data. Performing initial full training.")
        train_or_finetune_classifier(force_retrain_all_from_training_data=True)
    elif classifier_model is None:
        print(f"\nNot enough seed data in training_data ({len(training_data)}/{MIN_SAMPLES_FOR_TRAINING}) "
              f"for initial training with {EMBEDDER_TYPE}. Collect more feedback via processing tags.")
        
    # add_manual_correction("hat", "ACCESSORY") # Example of manual correction
    # add_manual_correction("baseball_cap", "ACCESSORY") # Example of manual correction

    post = ""
    postTags = gb.filterTagsCategory(gb.getPostTags(post), [0])

    # --- Test processing some image tags (Interactive Feedback Loop) ---
    test_image_tags_batch = [
        postTags,
    ]

    processed_tags = []

    for i, image_tags in enumerate(test_image_tags_batch):
        print(f"\n--- Processing Image {i+1} Tags ---")
        filtered_tags_for_image = []
        for tag in image_tags:
            # Use the new function. It will handle feedback and retraining internally if needed.
            # The 'allow_interactive_feedback' flag can be set to False if you
            # just want to see its initial prediction without stopping for feedback in some contexts.
            final_category_after_gate = get_prediction_with_confidence_gate(tag, allow_interactive_feedback=True)
            
            print(f"    Tag '{tag}' -> Final Category after Gate: '{final_category_after_gate}'")

            if final_category_after_gate in ["POSE_COMPOSITION","ATTIRE", "ACCESSORY"]: # Or other categories you want to keep
                 filtered_tags_for_image.append(tag)
            elif final_category_after_gate not in ["NEEDS_INITIALIZATION", "NEEDS_TRAINING", "ERROR_CLASS_MISMATCH", "ERROR_PREDICTION", None]:
                 print(f"    Filtering out '{tag}' (Category: {final_category_after_gate})")
            else:
                 print(f"    Could not reliably categorize '{tag}' (Status: {final_category_after_gate})")

        print(f"Filtered Pose/Composition for Image {i+1}: {filtered_tags_for_image}")
        processed_tags.append(",".join(filtered_tags_for_image))

    # --- Final check for remaining feedback ---
    if feedback_buffer:
        print("\nProcessing remaining feedback buffer before exit...")
        train_or_finetune_classifier()
    
    # --- Example of final predictions on a test set ---
    print(f"\n--- Final Predictions using {EMBEDDER_TYPE} on a test set: ---")
    if classifier_model:
        final_prompt = ""
        final_test_tags = []
        for tst_tag in final_test_tags:
            cat, conf = predict_tag(tst_tag)
            print(f"'{tst_tag}' -> Prediction: '{cat}' (Confidence: {conf:.2f})")
            if cat in ["POSE_COMPOSITION","ATTIRE", "ACCESSORY"]:
                final_prompt += f"{tst_tag}, "
        print(final_prompt[:-2])
    else:
        print(f"Keras model for {EMBEDDER_TYPE} was not trained or loaded, so no final predictions to show.")

    for processed_tag in processed_tags:
        print(f"Processed Tag: {processed_tag}")

    # Persist all accumulated training_data at the end
    # training_data_save_path = os.path.join(MODEL_DIR, "all_training_data.pkl")
    # try:
    #     with open(training_data_save_path, 'wb') as f:
    #         pickle.dump(training_data, f)
    #     print(f"\nSaved all {len(training_data)} training samples to {training_data_save_path}")
    # except Exception as e:
    #     print(f"Error saving training_data: {e}")