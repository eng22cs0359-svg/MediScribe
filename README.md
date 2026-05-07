# MediScribe

## What is MediScribe?
A system that can convert doctor's handwritten prescriptions into machine-readable text and classify the medicines along with their doses. It will also send an alert to the patient's registered email address containing all the relevant prescription details.

Key features:
* AWS Textract: Extracts text from doctor's handwritten prescriptions.
* NER Model: Classifies the extracted text into relevant categories.
* Alert System: Sends an email alert containing all the prescription details (medicines, doses, and category) to the patient's registered email address.

**Output:** Structured data with medicine names, dosages, and schedules extracted from the text.

## Technologies Used
- Python
- Natural Language Processing (NLP) techniques
- AWS Textract 
- Named Entity Recognition (NER) techniques
- Machine Learning Algorithms

## Usage
1. Upload or provide the handwritten prescription image to the system.
2. The system will process the image, extract text, classify it and get the medicine names and dosages along with their schedule.
3. The application will send you email reminders when it's time to take your medication, based on your scheduled dosage timings.

## Contributing
1. Fork the repository.
2. Create a new branch (git checkout -b feature-branch).
3. Commit your changes (git commit -m 'Add some feature').
4. Push to the branch (git push origin feature-branch).
5. Open a pull request.

## License
This project is licensed under the [MIT License](https://github.com/Gupta-Aryaman/scanPlus/blob/main/LICENSE).
