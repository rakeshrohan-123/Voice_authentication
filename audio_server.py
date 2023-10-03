import os, base64, boto3, pymongo
import nemo.collections.asr as nemo_asr
from fastapi import FastAPI, UploadFile, Form
from typing import List
from collections import OrderedDict
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
AWS_BUCKET_NAME = ""
AWS_REGION = ""
AWS_ACCESS_KEY = ""
AWS_SECRET_KEY = ""
base_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/"
AWS_S3_FOLDER = ""

MONGO_CONNECTION_STRING = ""
MONGO_DB_NAME = ""
MONGO_COLLECTION_NAME = ""




client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
db = client[MONGO_DB_NAME]
collection = db[MONGO_COLLECTION_NAME]


s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

def base64_to_wav(base64_string, output_file_path):
    base64_decoded = base64.b64decode(base64_string)
    with open(output_file_path, "wb") as output_file:
        output_file.write(base64_decoded)

def verify_speaker(model, sample_file, reference_file):
    result = model.verify_speakers(sample_file, reference_file)
    return result

speaker_model = nemo_asr.models.EncDecSpeakerLabelModel.from_pretrained("nvidia/speakerverification_en_titanet_large")

audio_folder = "user_audio_files"
audio_folder1= "audio_data"\
@app.post("/signin/")
async def signin(
    audio_file: str = Form(None)
):
    try:
        print("hit successful")
        temp_audio_path = "temp_audio.wav"
        base64_to_wav(audio_file, temp_audio_path)
        # Compare the uploaded audio file with existing folder files and return top 3 matches
        results = []
        for existing_file in os.listdir(audio_folder):
            print("working")
            result = verify_speaker(speaker_model, temp_audio_path, os.path.join(audio_folder, existing_file))
            if result>0.81:
                print(result)
                results.append((existing_file, result))
        #return results
        if len(results)==0:
            return {"message": "Signin Failed"}
        print(results)

        results.sort(key=lambda x: x[1], reverse=True)
        print("result of the data are, ", results)
        top_matches = [result[0] for result in results[:1]]
        print(top_matches)
        top_matche= top_matches[0]
        print(type(top_matche))
        print(top_matche)
        output= top_matche.split("_")
	query = {
                        "parentsmobileno": output[0]
                }

        result = collection.find_one(query)
        data= result['child'][int(output[1][:1])-1]
        student_name= data['childname']

        medium_of_instruction= data["mediumofinstruction"]

        grade= data['childclass']
        curriculum= data['childsyllabus']
        profile_img=data['childimageurl']

        return OrderedDict({"success": True, "student_name": student_name,
        "medium_of_instruction": medium_of_instruction,
        "grade": grade,
        "curriculum": curriculum,
        "profile_img":profile_img
        })
        # return {"message": "Signin successful", "mobile": output[0], "child": output[1][:1]}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
    
