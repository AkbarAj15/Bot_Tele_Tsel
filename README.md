# BOT TELEGRAM WITH PYTHON : Telkomsel Bot User
Repository for Telegram Bot using Python.
## Overview
By using this Machine Learning model, it is hoped that it can provide scholarship recommendations based on user personal data so that it can help prospective scholarship recipients to register themselves for the right scholarship or suitable for them.

## Table of Contents

- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
  - [Data Preparation](#data-preparation)
  - [Clustering](#clustering)
  - [Model Training](#model-training)
  - [Model Evaluation](#model-evaluation)
- [Results](#results)
- [License](#license)

## Getting Started

### Prerequisites
To install all the libraries needed in this model, use the syntax below:
```bash
pip install -r requirements.txt
```
### Installation
```bash
# Clone the repository
git clone https://github.com/CH2-PS562-Grant-Me/MachineLearningGM.git

# Change directory
cd MachineLearningGM # change with your folder name

# Install dependencies
pip install -r requirements.txt
```
## Usage

In the process of making this model, there are several stages that are carried out and the use of the required data.

### Data Preparation
For the dataset that we use in csv format, which has several data columns including:
- GPA value
- Number of certifications
- Number of professional certifications
- Number of national achievements
- Number of national top 3 competitions
- Number of international achievements
- Number of international top 3 competitions
- Total internship experience (number of months)
- Total committee experience (number of months)

After getting the dataset, data cleaning is carried out starting from separating data from semicolons, replacing empty values to NaN, and changing all data types to float.

### Clustering
We use the K-Means algorithm to cluster each data in the dataset.
```bash
# Create a k-means model with the desired number of clusters
kmeans = KMeans(n_clusters=5, random_state=42)

# Add the clustering result column to the dataframe
data['Cluster'] = kmeans.labels_
```
There are 5 clusters initialized, each cluster representing the scholarship types below.
- cluster[0] = government tag
- cluster[1] = private tag
- cluster[2] = organization tag
- cluster[3] = achievement tag
- cluster[4] = aid tag

### Model Training
For the model training process, we used tensorflow.keras which uses 3 hidden layers. Which will be compiled using *adam* optimizer and loss params *sparse_categorical_crossentropy*.
```bash
# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X_scaled, data['Cluster'], test_size=0.2, random_state=42)

# Define the TensorFlow model
model = tf.keras.Sequential([
    tf.keras.layers.Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(5, activation='softmax')
])

# Compile the model
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
```
### Model Evaluation
To evaluate the model, we first train it for 10 iterations or epochs. then we evaluate it based on the train and testing data.
```bash
# Train the model
model.fit(X_train, y_train, epochs=10, batch_size=32, verbose=1, validation_data=(X_test, y_test))

# Evaluate the model
test_loss, test_accuracy = model.evaluate(X_test, y_test)
```
## Results
To check the result, we will try to fill the random input into the model first.
```bash
# Inputan baru untuk diprediksi
new_input = np.array([[3.8, 5, 3, 2, 1, 1, 1, 14, 13]])  # Ganti dengan inputan yang sesuai

# Lakukan standardisasi pada inputan baru
new_input_scaled = scaler.transform(new_input)

# Lakukan prediksi cluster
predicted_cluster = kmeans.predict(new_input_scaled)

# Tampilkan hasil prediksi
print("Inputan masuk ke cluster:", predicted_cluster)
if predicted_cluster == 0:
    print("Pemerintah")
elif predicted_cluster == 1:
    print("Swasta")
elif predicted_cluster == 2:
    print("Organisasi")
elif predicted_cluster == 3:
    print("Prestasi")
elif predicted_cluster == 4:
    print("Bantuan")
```
*output :* 
*Inputan masuk ke cluster: [1]
Swasta*

## License
Copyright © 2023 Pakintaki Group . All rights reserved.



