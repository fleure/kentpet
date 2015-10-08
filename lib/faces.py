from random import choice

def generate_face():
    with open("attributes/ears") as f:
        ears = [line.rstrip() for line in f if len(line) <= 3]
    ear = choice(ears)
    
    with open("attributes/mouth") as f:
        mouths = [line.rstrip() for line in f if len(line) <= 2]
    mouth = choice(mouths)

    with open("attributes/eyes") as f:
        eyes = [line.rstrip() for line in f if len(line) <= 3]
    eye = choice(eyes)

    face = {}
    face['mouth'] = mouth
    face['eyes'] = eye
    face['ears'] = ear

    return face

def get_face(pet):
    try:
        ear = pet['ears']
        eye = pet['eyes']
        mouth = pet['mouth']
    except KeyError:
        return
    face = ear[0] + eye[0] + mouth
    if len(eye) > 1:
        face += eye[1]
    else:
        face += eye[0]

    if len(ear) > 1:
        face += ear[1]
    else:
        face += ear[0]

    return face

def get_face_attributes():
    return ["mouth", "eyes", "ears"]
