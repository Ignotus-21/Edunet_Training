# import streamlit as st
# # from clarifai import ApiClient
# from palm import Palm2
# import cv2 


# Initialize APIs
# clarifai_app = ApiClient(api_key='bbd0fd68e75e4bcdb6402ed2d736f6ac')
# palm2_client = Palm2(api_key='AIzaSyDzOOp7f6UaVyB6KauU0TWIsH8FwdjbVBM')

import streamlit as st
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2, service_pb2_grpc
# from palm import Palm
from palm_module import Palm
import cv2
from tqdm import tqdm

# Initialize Clarifai channel
channel = ClarifaiChannel.get_grpc_channel()
stub = service_pb2_grpc.V2Stub(channel)

# Initialize PaLM 2 client (replace 'YOUR_PALM_API_KEY' with your actual PaLM 2 API key)
palm2_client = Palm(api_key='AIzaSyDzOOp7f6UaVyB6KauU0TWIsH8FwdjbVBM')

# Capture webcam video
capture_button = st.button("Capture Food")
stop_button = st.button("Stop Capture", disabled=True)
manual_button = st.button("Identify Manually")

video_frame = None
manual_food = None

if capture_button:
    video_frame = st.image(st.camera_capture(), caption="Captured Food", use_column_width=True)
    stop_button.disabled = False
elif stop_button:
    video_frame = None
    stop_button.disabled = True

if manual_button:
    manual_food = st.text_input("Enter food name:")

# Image preview and confirmation
if video_frame is not None:
    if st.button("Process Food"):
        # Convert to RGB and process
        rgb_frame = cv2.cvtColor(video_frame, cv2.COLOR_BGR2RGB)

        # Clarifai food recognition (replace 'YOUR_CLARIFAI_API_KEY' with your actual Clarifai API key)
        metadata = (('authorization', 'Key YOUR_CLARIFAI_API_KEY'),)
        response = stub.PostModelOutputs(
            service_pb2.PostModelOutputsRequest(
                model_id='food-items-v1.0',
                inputs=[
                    service_pb2.Input(data=service_pb2.Data(image=service_pb2.Image(url=video_frame)))
                ]
            ),
            metadata=metadata
        )

        # Extract top label from Clarifai response
        top_label = response.outputs[0].data.concepts[0].name if response.outputs else manual_food

        # Dietary preferences
        dietary_preferences = st.text_input("Dietary preferences (optional):")

        # PaLM 2 reuse suggestions
        st.info("Processing... This may take a moment.")
        response = palm2_client.generate(
            prompts=["How to reuse leftover " + top_label + "?"],
            temperature=0.7,
            top_k=3,
        )

        st.success("Processing Complete!")

        # Formatting and display results
        st.markdown("*Identified Food:* " + top_label)
        st.write("**Reuse Ideas for your Leftover " + top_label + ":**")
        for text in response["completions"]:
            st.write("- " + text, style={"color": "#0095ff"})

        # Filter suggestions based on preferences (optional)
        if dietary_preferences:
            # Implement filtering logic here
            st.write("Filtered suggestions based on your preferences...")

else:
    st.write("Capture your leftover food or enter the name manually.")