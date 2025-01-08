import anthropic
import os
import json
from uuid import uuid4
import openai


def evaluate_claude(in_dir, out_dir):
    api_key = os.getenv("API_KEY")
    if api_key is None:
        if os.path.exists("api_key.txt"):
            with open("api_key.txt", "r") as f:
                api_key = f.read().strip()

    model = "claude-3-5-sonnet-latest"
    client = anthropic.Anthropic(api_key=api_key)

    system_text = "You will evaluate a conversation between a beginner level student who wants to learn a new language and a language teaching tutor system. After you get the conversation, you should evaluate each aspect of the system regarding the questionary provided."

    user_message = ("""The conversation between a beginner level student and the language teaching tutor system is as follows:\n{}\nRegarding this conversation please complete the following questionary. You need to assess the performance of the system only. If you completely agree with the given statement as if you are the student, you should give 10 points. If you completely disagree with the given statement as if you are the student, you should give 1 point. Give the results in the 'number-> point' structure.\nQUESTIONARY: 
        1-> I was able to easily access the desired modules whenever I want:
        2-> I was able to easily select the topics I wanted:
        3-> The instructions provided by the system were clear and understandable:
        4-> The course contents were clear and understandable:
        5-> The course contents were efficient and directly related to the chosen topic:
        6-> I received effective answers to the questions I asked during the lesson:
        7-> The quiz questions were directly related to the course content:
        8-> The feedback after the quizzes was accurate:
        9-> The explanations after the quizzes (if any) helped me address unclear points:
        10-> I was satisfied with the overall experience:""")
    for name in os.listdir(in_dir):
        if name == '.DS_Store':
            continue
        with open(f'{in_dir}/{name}', 'r') as f:
            conversation = json.load(f)
        conversation_id = name.split('.')[0]
        evaluation_id = uuid4()
        output_path = f'{out_dir}/{conversation_id}_claude_{evaluation_id}.txt'

        conversation_text = ""
        last_speaker = ""
        for message in conversation['conversation']:
            speaker = message["role"]
            if speaker == "system":
                speaker = "SYSTEM:"
            elif speaker == "user":
                speaker = "STUDENT:"
            elif speaker == "quiz":
                speaker = "QUIZ:"
            elif speaker == "quiz_answer":
                speaker = "STUDENT'S QUIZ ANSWERS:"
            if speaker != last_speaker:
                conversation_text += speaker + "\n"
            last_speaker = speaker
            conversation_text += message['message'].strip() + "\n"
        current_message = user_message.format(conversation_text)
        message = client.messages.create(
            model = model,
            max_tokens = 1000,
            temperature = 0.1,
            system = system_text,
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": current_message
                        }
                    ]
                }
            ]
        )

        result = message.content[0].text
        with open(output_path, "w") as f:
            f.write(result)
        print(output_path)



def evaluate_gpt(in_dir, out_dir):
    api_key = os.getenv("API_KEY_EVAL")
    if api_key is None:
        if os.path.exists("api_key_eval.txt"):
            with open("api_key_eval.txt", "r") as f:
                api_key = f.read().strip()

    model = "gpt-4o"
    openai.api_key = api_key

    system_text = "You will evaluate a conversation between a beginner level student who wants to learn a new language and a language teaching tutor system. After you get the conversation, you should evaluate each aspect of the system regarding the questionary provided."

    user_message = ("""The conversation between a beginner level student and the language teaching tutor system is as follows:\n{}\nRegarding this conversation please complete the following questionary. You need to assess the performance of the system only. If you completely agree with the given statement as if you are the student, you should give 10 points. If you completely disagree with the given statement as if you are the student, you should give 1 point. Give the results in the 'number-> point' structure.\nQUESTIONARY: 
        1-> I was able to easily access the desired modules whenever I want:
        2-> I was able to easily select the topics I wanted:
        3-> The instructions provided by the system were clear and understandable:
        4-> The course contents were clear and understandable:
        5-> The course contents were efficient and directly related to the chosen topic:
        6-> I received effective answers to the questions I asked during the lesson:
        7-> The quiz questions were directly related to the course content:
        8-> The feedback after the quizzes was accurate:
        9-> The explanations after the quizzes (if any) helped me address unclear points:
        10-> I was satisfied with the overall experience:""")
    for name in os.listdir(in_dir):
        if name == '.DS_Store':
            continue
        with open(f'{in_dir}/{name}', 'r') as f:
            conversation = json.load(f)
        conversation_id = name.split('.')[0]
        evaluation_id = uuid4()
        output_path = f'{out_dir}/{conversation_id}_gpt_{evaluation_id}.txt'

        conversation_text = ""
        last_speaker = ""
        for message in conversation['conversation']:
            speaker = message["role"]
            if speaker == "system":
                speaker = "SYSTEM:"
            elif speaker == "user":
                speaker = "STUDENT:"
            elif speaker == "quiz":
                speaker = "QUIZ:"
            elif speaker == "quiz_answer":
                speaker = "STUDENT'S QUIZ ANSWERS:"
            if speaker != last_speaker:
                conversation_text += speaker + "\n"
            last_speaker = speaker
            conversation_text += message['message'].strip() + "\n"
        current_message = user_message.format(conversation_text)
        response = openai.ChatCompletion.create(
            model=model,
            max_completion_tokens = 1000,
            temperature = 0.1,
            messages = [
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "text",
                            "text": system_text
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": current_message
                        }
                    ]
                }
            ]
        )

        result = response.choices[0].message["content"]
        with open(output_path, "w") as f:
            f.write(result)
        print(output_path)


if __name__ == '__main__':

    evaluate_claude('selected_conversations', 'selected_conversation_evaluations')
    evaluate_gpt('selected_conversations', 'selected_conversation_evaluations')
