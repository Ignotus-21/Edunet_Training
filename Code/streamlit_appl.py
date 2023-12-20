import streamlit as st
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2
from PIL import Image

# Clarifai API code
def predict_food_item(image_bytes, pat, user_id, app_id, model_id, model_version_id):
    channel = ClarifaiChannel.get_grpc_channel()
    stub = service_pb2_grpc.V2Stub(channel)

    metadata = (('authorization', 'Key ' + pat),)

    userDataObject = resources_pb2.UserAppIDSet(user_id=user_id, app_id=app_id)

    post_model_outputs_response = stub.PostModelOutputs(
        service_pb2.PostModelOutputsRequest(
            user_app_id=userDataObject,
            model_id=model_id,
            version_id=model_version_id,
            inputs=[
                resources_pb2.Input(
                    data=resources_pb2.Data(
                        image=resources_pb2.Image(
                            base64=image_bytes
                        )
                    )
                )
            ]
        ),
        metadata=metadata
    )

    if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
        print(post_model_outputs_response.status)
        raise Exception("Post model outputs failed, status: " + post_model_outputs_response.status.description)

    output = post_model_outputs_response.outputs[0]
    return output

# Streamlit application code
st.title("Food Recognition App")

# Sidebar option to choose between camera or upload
option = st.sidebar.radio("Choose an option", ["Capture from Camera", "Upload Image"])

# Function to capture image from camera
def capture_from_camera():
    st.markdown("### Capture Image")
    captured_image = st.camera_input("Capture Image")
    return captured_image

# Function to upload image
def upload_image():
    st.markdown("### Upload Image")
    uploaded_file = st.file_uploader("Choose a file", type=["jpg", "jpeg", "png"])
    return uploaded_file

# Choose capture method based on user option
if option == "Capture from Camera":
    captured_image = capture_from_camera()
elif option == "Upload Image":
    uploaded_file = upload_image()

# Display the selected image for food recognition
if st.button("Recognize Food"):
    if option == "Capture from Camera" and captured_image is not None:
        # Convert the captured image to bytes
        image_bytes = captured_image.getvalue()
        # Display the captured image at its standard size
        st.image(captured_image, caption="Captured Image", use_column_width=True)
    elif option == "Upload Image" and uploaded_file is not None:
        # Read the uploaded image file buffer as bytes
        image_bytes = uploaded_file.read()
        # Display the uploaded image at its standard size
        st.image(Image.open(uploaded_file), caption="Uploaded Image", use_column_width=True)

    # Get Clarifai predictions using the defined function
    st.markdown("### Predicted Concepts:")
    pat = 'ac76a2d4778541baa55aa743c79f00dc'  # Replace with your PAT
    user_id = 'clarifai'
    app_id = 'main'
    model_id = 'food-item-v1-recognition'
    model_version_id = 'dfebc169854e429086aceb8368662641'

    predicted_output = predict_food_item(
        image_bytes, pat, user_id, app_id, model_id, model_version_id
    )

    # Display predicted concepts horizontally
    concepts = [f"{concept.name} {concept.value:.2f}" for concept in predicted_output.data.concepts]
    st.write(", ".join(concepts))



# import streamlit as st
# from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
# from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
# from clarifai_grpc.grpc.api.status import status_code_pb2
# from PIL import Image

# # Clarifai API code
# def predict_food_item(image_bytes, pat, user_id, app_id, model_id, model_version_id):
#     channel = ClarifaiChannel.get_grpc_channel()
#     stub = service_pb2_grpc.V2Stub(channel)

#     metadata = (('authorization', 'Key ' + pat),)

#     userDataObject = resources_pb2.UserAppIDSet(user_id=user_id, app_id=app_id)

#     post_model_outputs_response = stub.PostModelOutputs(
#         service_pb2.PostModelOutputsRequest(
#             user_app_id=userDataObject,
#             model_id=model_id,
#             version_id=model_version_id,
#             inputs=[
#                 resources_pb2.Input(
#                     data=resources_pb2.Data(
#                         image=resources_pb2.Image(
#                             base64=image_bytes
#                         )
#                     )
#                 )
#             ]
#         ),
#         metadata=metadata
#     )

#     if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
#         print(post_model_outputs_response.status)
#         raise Exception("Post model outputs failed, status: " + post_model_outputs_response.status.description)

#     output = post_model_outputs_response.outputs[0]
#     return output

# # Streamlit application code
# st.title("Food Recognition App")

# # Sidebar option to choose between camera or upload
# option = st.sidebar.radio("Choose an option", ["Capture from Camera", "Upload Image"])

# # Function to capture image from camera
# def capture_from_camera():
#     st.markdown("### Capture Image")
#     captured_image = st.camera_input("Capture Image")
#     return captured_image

# # Function to upload image
# def upload_image():
#     st.markdown("### Upload Image")
#     uploaded_file = st.file_uploader("Choose a file", type=["jpg", "jpeg", "png"])
#     return uploaded_file

# # Choose capture method based on user option
# if option == "Capture from Camera":
#     captured_image = capture_from_camera()
# elif option == "Upload Image":
#     uploaded_file = upload_image()

# # Display the selected image for food recognition
# if st.button("Recognize Food"):
#     if option == "Capture from Camera" and captured_image is not None:
#         # Convert the captured image to bytes
#         image_bytes = captured_image.getvalue()
#         # Display the captured image at its standard size
#         st.image(captured_image, caption="Captured Image", use_column_width=True)
#     elif option == "Upload Image" and uploaded_file is not None:
#         # Read the uploaded image file buffer as bytes
#         image_bytes = uploaded_file.read()
#         # Display the uploaded image at its standard size
#         st.image(Image.open(uploaded_file), caption="Uploaded Image", use_column_width=True)

#     # Get Clarifai predictions using the defined function
#     st.markdown("### Predicted Concepts:")
#     pat = 'ac76a2d4778541baa55aa743c79f00dc'  # Replace with your PAT
#     user_id = 'clarifai'
#     app_id = 'main'
#     model_id = 'food-item-v1-recognition'
#     model_version_id = 'dfebc169854e429086aceb8368662641'

#     predicted_output = predict_food_item(
#         image_bytes, pat, user_id, app_id, model_id, model_version_id
#     )

#     # Display predicted concepts horizontally
#     concepts = [f"{concept.name} {concept.value:.2f}" for concept in predicted_output.data.concepts]
#     st.write(", ".join(concepts))

#     # Display a separate section for concepts with value above or equal to 0.85
#     st.markdown("### High Confidence Concepts:")
#     high_confidence_concepts = [f"{concept.name} {concept.value:.2f}" for concept in predicted_output.data.concepts if concept.value >= 0.85]
#     st.write(", ".join(high_confidence_concepts))

# import pathlib
# import textwrap
# import google.generativeai as genai
# from IPython.display import display
# from IPython.display import Markdown

# def to_markdown(text):
#   text = text.replace('•', '  *')
#   return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

# GOOGLE_API_KEY = 'AIzaSyDJ4815fNqfkwvpp4m6qCXjmU9V8QoTaWw'  # Replace with your API key

# # Configure the generative AI service
# genai.configure(api_key=GOOGLE_API_KEY)




# this is working

# import streamlit as st
# from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
# from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
# from clarifai_grpc.grpc.api.status import status_code_pb2
# from PIL import Image
# import textwrap
# import google.generativeai as genai
# from IPython.display import Markdown

# def predict_food_item(image_bytes, pat, user_id, app_id, model_id, model_version_id):
#     channel = ClarifaiChannel.get_grpc_channel()
#     stub = service_pb2_grpc.V2Stub(channel)

#     metadata = (('authorization', 'Key ' + pat),)

#     userDataObject = resources_pb2.UserAppIDSet(user_id=user_id, app_id=app_id)

#     post_model_outputs_response = stub.PostModelOutputs(
#         service_pb2.PostModelOutputsRequest(
#             user_app_id=userDataObject,
#             model_id=model_id,
#             version_id=model_version_id,
#             inputs=[
#                 resources_pb2.Input(
#                     data=resources_pb2.Data(
#                         image=resources_pb2.Image(
#                             base64=image_bytes
#                         )
#                     )
#                 )
#             ]
#         ),
#         metadata=metadata
#     )

#     if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
#         print(post_model_outputs_response.status)
#         raise Exception("Post model outputs failed, status: " + post_model_outputs_response.status.description)

#     output = post_model_outputs_response.outputs[0]
#     return output

# # Streamlit application code


# st.title("Gastronomix AI: Culinary Insight Hub")



# st.markdown(
#     """
#     <span style="font-size: 18px;"> Gastronomix AI stands as an innovative food inventory management solution, 
#     incorporating cutting-edge technology to minimize food waste and enhance user convenience. Bid farewell to 
#     uncertainties when managing leftovers; Culinary Guardian steps in as your culinary ally. Utilize the phone's camera 
#     or manual text entry to seamlessly identify food products. With its state-of-the-art object recognition, Culinary 
#     Guardian redefines culinary management, ensuring a smooth and efficient experience in organizing your kitchen inventory.</span>
#     """,
#     unsafe_allow_html=True
# )

# # page_bg_img = f"""
# # <style>
# # [data-testid="stAppViewContainer"] > .main {{
# # background-image: url("https://i.postimg.cc/Df66JRLg/logo-black.jpg");
# # background-size: cover;
# # background-position: center center;
# # background-repeat: no-repeat;
# # background-attachment: local;
# # }}
# # [data-testid="stHeader"] {{
# # background: rgba(0,0,0,0);
# # }}
# # </style>
# # """

# # st.markdown(page_bg_img, unsafe_allow_html=True)

# # Sidebar option to choose between camera or upload
# option = st.sidebar.radio("Choose an option", ["Capture from Camera", "Upload Image"])

# # Function to capture image from camera
# def capture_from_camera():
#     st.markdown("### Capture Image")
#     capture_button = st.button("Capture Image")
    
#     if capture_button:
#         captured_image = st.camera_input("Captured Image")
#         return captured_image
#     else:
#         return None
#     # st.markdown("### Capture Image")
#     # captured_image = st.camera_input("Capture Image")
#     # return captured_image

# # Function to upload image
# def upload_image():
#     # upload_button = st.button("Upload Image")
    
#     # if upload_button:
#     #     captured_image = st.file_uploader("Choose a file", type=["jpg", "jpeg", "png"])
#     #     return uploaded_file
#     # else:
#     #     return None
#     st.markdown("### Upload Image")
#     uploaded_file = st.file_uploader("Choose a file", type=["jpg", "jpeg", "png"])
#     return uploaded_file

# # Choose capture method based on user option
# if option == "Capture from Camera":
#     captured_image = capture_from_camera()
#     if captured_image is not None:
#         # Convert the captured image to bytes
#         image_bytes = captured_image.getvalue()
# elif option == "Upload Image":
#     uploaded_file = upload_image()
#     if uploaded_file is not None:
#         # Read the uploaded image file buffer as bytes
#         image_bytes = uploaded_file.read()

# # Display the selected image for food recognition
# if st.button("Recognize Food"):
#     if 'image_bytes' not in locals():
#         st.markdown("### Please capture or upload an image")
#         st.stop()

#     # Get Clarifai predictions using the defined function
#     st.markdown("### Predicted Concepts:")
#     pat = 'ac76a2d4778541baa55aa743c79f00dc'  # Replace with your PAT
#     user_id = 'clarifai'
#     app_id = 'main'
#     model_id = 'food-item-v1-recognition'
#     model_version_id = 'dfebc169854e429086aceb8368662641'

#     predicted_output = predict_food_item(
#         image_bytes, pat, user_id, app_id, model_id, model_version_id
#     )

#     # Display predicted concepts horizontally
#     concepts = [f"{concept.name} {concept.value:.2f}" for concept in predicted_output.data.concepts]
#     st.write(", ".join(concepts))

#     # Display a separate section for concepts with value above or equal to 0.85
#     st.markdown("### High Confidence Concepts:")
#     high_confidence_concepts = [f"{concept.name} {concept.value:.2f}" for concept in predicted_output.data.concepts if concept.value >= 0.85]
#     st.write(", ".join(high_confidence_concepts))

# # New section for generating recipe suggestions
# st.sidebar.markdown("## Recipe Suggestions")

# # Get user input for the ingredient
# ingredient_prompt = st.sidebar.text_input("Enter ingredients to recieve recipe:", "")

# def to_markdown(text):
#   text = text.replace('•', '  *')
#   return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

# GOOGLE_API_KEY='AIzaSyDJ4815fNqfkwvpp4m6qCXjmU9V8QoTaWw'
# genai.configure(api_key=GOOGLE_API_KEY)

# # Create a button to trigger recipe generation
# if st.sidebar.button("Generate Recipes"):
#     # Use the generative AI model to generate content
#     model = genai.GenerativeModel('gemini-pro')
#     response = model.generate_content(f"what recipes can I make with {ingredient_prompt}")

#     # Display the generated content
#     st.sidebar.markdown("### Recipe Suggestions:")
#     st.sidebar.markdown(response.text)

