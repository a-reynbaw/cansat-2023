# V-Space for CanSat in Europe 2023
This repository contains code from team V-Space's (which I was part of) participation in the CanSat in Greece and CanSat in Europe 2023 contest. The team managed to recieve the "Best CanSat Project" award in the local contest and the "Highest Technical Achievment Award" in the European one.

This contest has educational purpose and it is addressed to highschool students. Its objectives are to build a small satelite ( the size of a soda can ), which will be launched at the hight of 1km and will have to complete 2 missions:

1) a primary mission, which is common for every participating team and it's goal is to recieve temperatue and atmosperic pressure data via telecommunication allong with a successful retrival of the CanSat after its landing.

2) the secondary mission is up for each team to decide.

For our secondary mission, we implemented a telecommunicational network which contains:

- the cansat (CS)

- the ground station (GS)

- three gound devices (Device A/ DA, Device B/ DB, Litte House/ LH)

The CanSat is kind of like a prototype of what would be a geostatical satellite that would provide services to a community, such as:

- ensure communications security, through end-to-end encryption

- monitor a forest area through a trained neural network which takes pictures and analyses the for any signes of fire 

- provide data for conducting scientific experiments (we calculated the accelaration of gravity)

## CanSat
The CanSat code was written in Python and runs on a Raspberry 0. The code was mainly written by us, limiting librarys to those required by electrical components (GPS, BMP, LoRa etc.)

### Encryption
The encryption is achieved through a combination of assymetric (RSA algorithm) and symmentric (Hill algorithm) encryption

At first, the keys for the symmetric encryption are sent via a handshake, using asymmetric encryption. After the handshake, all messages are encrypted in three layers:

1. the message is encrypted with the sender's private assymetric keys. This serves as a digital signature, to ensure integrity.

2. the origina sender allong with the already encrypted message, are encrypted using the final reciever's public key. This is done to ensure authenticity.

3. the final reciever along with the already encrypted message, are encrypted with the symmetric keys used for the communication between an intermediate node, that serves the final reciever (either GS or CS), and the final reciever. 

The first two nodes of the message the message, which contain the current sender (either original or intermediate) and the next reciever, respectively remain un-encrypted.

### Neural Network
The Newral Network used for this project is an MLP (Multi-Layer Perceptron), which has been trained in our lab using data-sets found on the internet. On the CanSat runs only the prediction program.