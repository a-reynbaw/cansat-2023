# V-Space for CanSat in Europe 2023
This repository contains the code from team V-Space's participation in the CanSat in Greece and CanSat in Europe 2023 contests, of which I was a member. The team received the "Best CanSat Project" award in the local contest and the "Highest Technical Achievement Award" in the European competition.

This contest is educational in nature and is aimed at high school students. Its objective is to build a small satellite (the size of a soda can), which will be launched to an altitude of 1 km and will have to complete two missions:

1) A primary mission, which is common for all participating teams. Its goal is to collect temperature and atmospheric pressure data via telecommunication, along with the successful retrieval of the CanSat after its landing.

2) A secondary mission, which is determined by each team.

For our secondary mission, we implemented a telecommunication network consisting of:

- The CanSat (CS)
- The ground station (GS)
- Three ground devices (Device A/DA, Device B/DB, Little House/LH)

The CanSat serves as a prototype for a geostationary satellite that could provide services to a community, such as:

- Ensuring communication security through end-to-end encryption.
- Monitoring a forest area using a trained neural network that analyzes images for signs of fire.
- Providing data for conducting scientific experiments (e.g., calculating the acceleration due to gravity).

## CanSat
The CanSat code was written in Python and runs on a Raspberry Pi Zero. The code was primarily developed by our team, with external libraries limited to those required by the electrical components (e.g., GPS, BMP, LoRa, etc.).

### Encryption
Encryption is achieved through a combination of asymmetric (RSA algorithm) and symmetric (Hill algorithm) encryption.

Initially, the keys for symmetric encryption are exchanged via a handshake using asymmetric encryption. After the handshake, all messages are encrypted in three layers:

1. The message is encrypted with the sender's private asymmetric key. This acts as a digital signature to ensure integrity.
2. The original sender, along with the already encrypted message, is encrypted using the final receiver's public key. This ensures authenticity.
3. The final receiver, along with the already encrypted message, is encrypted with the symmetric keys used for communication between an intermediate node (either GS or CS) and the final receiver.

The first two nodes of the message, which contain the current sender (either original or intermediate) and the next receiver, respectively, remain unencrypted.

### Neural Network
The neural network used for this project is an MLP (Multi-Layer Perceptron), which was trained in our lab using publicly available datasets. On the CanSat, only the prediction program is executed.