import pandas as pd
import json

def create_dataframe(annotations_path):
    with open(annotations_path, 'r') as file:
        data = json.load(file)

    images = pd.DataFrame(data['images']).rename(columns={'id': 'image_id'})[['image_id', 'file_name']]

    categories = pd.DataFrame(data['categories'])[['id', 'name']]
    categories.rename(columns={'id': 'category_id'}, inplace=True)

    usecols = ['image_id', 'category_id']
    annotations = pd.DataFrame(data['annotations'])[usecols]

    dataframe = annotations.merge(categories, on='category_id').merge(images, on='image_id')[['file_name', 'name']]
    
    return dataframe

train_df = create_dataframe(r'/kaggle/input/food-recognition-2022/raw_data/public_training_set_release_2.0/annotations.json')
train_df

import os

splits = ['train', 'validation']

for split in splits:
    root = f'/kaggle/working/dataset/{split}'

    for index, row in train_df.iterrows():
        directory_name = row['name']
        directory_path = os.path.join(root, directory_name)

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

validation_df = create_dataframe(r'/kaggle/input/food-recognition-2022/raw_data/public_validation_set_2.0/annotations.json')
validation_df

import os
import shutil

def copy_images_to_destination(base_dir, dataframe, split):
    images_dir = os.path.join(base_dir, 'images')

    for index, row in dataframe.iterrows():
        file_name = row['file_name']
        file_class = row['name']

        dest_dir = os.path.join('/kaggle/working', 'dataset', split, file_class)
        os.makedirs(dest_dir, exist_ok=True)

        source_path = os.path.join(images_dir, file_name)
        destination_path = os.path.join(dest_dir, file_name)

        shutil.copyfile(source_path, destination_path)

    print("Done copying images.")

# copying training images to their respective classes

base_dir = '/kaggle/input/food-recognition-2022/raw_data/public_training_set_release_2.0'
dataframe = train_df
copy_images_to_destination(base_dir, dataframe, 'train')

# copying validation images to their respective classes

base_dir = '/kaggle/input/food-recognition-2022/raw_data/public_validation_set_2.0'
dataframe = validation_df
copy_images_to_destination(base_dir, dataframe, 'validation')

from tensorflow.keras.utils import image_dataset_from_directory as ImageDataset

train = ImageDataset(
    directory=r'/kaggle/working/dataset/train',
    label_mode='categorical',
    batch_size=32,
    image_size=(299, 299)
)

validation = ImageDataset(
    directory=r'/kaggle/working/dataset/validation',
    label_mode='categorical',
    batch_size=32,
    image_size=(299, 299)
)

element = validation.as_numpy_iterator().next()

x, y = element
x[0].shape, y[0].shape

import tensorflow as tf
from tensorflow.keras.applications import InceptionResNetV2
from tensorflow.keras.applications.inception_resnet_v2 import preprocess_input

# Define the learning rate
learning_rate = 0.001  # You can adjust this value as needed

strategy = tf.distribute.MirroredStrategy()

with strategy.scope():
    inception = InceptionResNetV2(include_top=False, weights='imagenet')
    inception.trainable = False

    inputs = tf.keras.Input(shape=(None, None, 3))
    x = preprocess_input(inputs)
    x = inception(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    outputs = tf.keras.layers.Dense(498, activation='softmax')(x)

    # Create the Adam optimizer with the specified learning rate
    optimizer = tf.keras.optimizers.Adam(learning_rate)

    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    
    model.summary()

    model.compile(optimizer=optimizer,
                  loss=tf.keras.losses.CategoricalCrossentropy(),
                  metrics=[tf.keras.metrics.CategoricalAccuracy()])


callback = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=8)

history = model.fit(train,
                    epochs=32,
                    validation_data=validation,
                    callbacks=[callback]
                   )
