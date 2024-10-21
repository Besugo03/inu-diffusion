import gradio as gr
import hugchat_test

def image_generate_description(image_path):
    descriptions_array = hugchat_test.image_description(image_path)
    return descriptions_array

## at the moment the number of outputs is fixed, but we can change it to be dynamic
outputs_array = [gr.Textbox(show_copy_button=True, label=f"Description {i}") for i in range(2)]

demo = gr.Interface(
    fn=image_generate_description,
    inputs=["text"],
    outputs=outputs_array
)

demo.launch()
