import anthropic
import re
import json
import os


def detect_name_and_language(user_response):
    message = client.messages.create(
        model = model,
        max_tokens = 1000,
        temperature = 0,
        system = "You are a name and mentioned language detector. You extract the initial name of the user in between <name> tags and detect which language the user wants to learn within <language> tags. If those information are not presented, do not give regarding information.",
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_response
                    }
                ]
            }
        ]
    )

    name = re.search(r"<name>.*</name>", message.content[0].text)
    if name is not None:
        name = name.group(0)[6:-7]

    language = re.search(r"<language>.*</language>", message.content[0].text)
    if language is not None:
        language = language.group(0)[10:-11]

    return name, language


def greeting():

    print("Hello there, I will be guiding you to learn any language you want in beginner level. Can you briefly mention about yourself and which language do you want to learn?")

    user_response = input()
    name, language = detect_name_and_language(user_response)

    while name is None or language is None:
        if name is None and language is None:
            print("Sorry, I didn't get your name and the language you're interested in. Can you provide these information?")
            user_response = input()
            name, language = detect_name_and_language(user_response)
        elif name is None:
            print("Sorry, I didn't get your name. Can you provide me your name, so I can speak with you more freely")
            user_response = input()
            name, _ = detect_name_and_language(user_response)
        elif language is None:
            print("Sorry, I didn't get the language you're interested in. To provide you the required language education, I need this information. What language do you want to learn?")
            user_response = input()
            _, language = detect_name_and_language(user_response)

    print(f"I am happy to meet you {name}\nLet's begin our {language} learning journey, shall we?")
    intention_history = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"My name is {name}, and I want to learn {language}."
                }
            ]
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": f"I am happy to meet you {name}\nLet's begin our {language} learning journey, shall we?"
                }
            ]
        }
    ]
    user_info = {
        "name": name,
        "language": language
    }
    return intention_history, user_info


def detect_user_intention(intention_history):

    tool_definition = {
        "name": "intention_detector",
        "description": "Retrieve's the intention of the user which uses a portal to learn a language. The intention is one of <proceed>, <quit>, <go_to_main_topics>, <go_to_sub_topics>, <exit_quiz>, <exit_lesson>, <proceed_to_quiz>.\n"
                       "<proceed>: The user wants to go to the next step.\n"
                       "<quit>: The user wants to exit the portal.\n"
                       "<go_to_main_topics>: The user wants to go to the main topic selection step. There are main topics covering the basics of regarding language.\n"
                       "<go_to_sub_topics>: The user wants to go to the sub topic selection step. A sub topic is one part of the previously selected main topic.\n"
                       "<exit_quiz>: The user wants to end the quiz step, the reason might also be finishing the quiz.\n"
                       "<exit_lesson>: The user wants to end the lesson for the selected topic.\n"
                       "<proceed_to_quiz>: The user wants to go to the quiz step.",
        "input_schema": {
            "type": "object",
            "properties": {
                "intention": {
                    "type": "string",
                    "description": "The intention of the user. It should one of the tags: <proceed>, <quit>, <go_to_main_topics>, <go_to_sub_topics>, <exit_quiz>, <exit_lesson>, <proceed_to_quiz>"
                }
            },
            "required": ["intention"]
        }
    }
    message = client.messages.create(
        model = model,
        max_tokens = 1000,
        temperature = 0,
        messages = intention_history,
        tools = [tool_definition]
    )

    if message.stop_reason == "tool_use":
        tool_response = message.content[-1].input['intention']
        for intention in intentions:
            if intention in tool_response and len(tool_response) <= len(intention) + 2:
                return intention
    return "proceed"


def main_topics_section(user_info):
    message = client.messages.create(
        model = model,
        max_tokens = 1000,
        temperature = 0,
        system = f"You are a professor who teaches elementary {user_info['language']}.",
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"My name is {user_info['name']}. Can you list the essential main topics for the elementary level of {user_info['language']}. List each topic name within <topic> tags."
                    }
                ]
            }
        ]
    )

    main_topics = []
    for topic in re.findall(r"<topic>.*</topic>", message.content[0].text):
        main_topics.append(topic[7:-8])

    return main_topics

def sub_topics_definition(user_info, main_topic):
    message = client.messages.create(
        model = model,
        max_tokens = 1000,
        temperature = 0,
        system = f"You are a professor who teaches elementary {user_info['language']}.",
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"My name is {user_info['name']}. I am beginner at {user_info['language']} language and want to learn more about {main_topic}. Can you list the essential sub topics that can be listed under the topic of {main_topic}? List each sub topic name within <sub_topic> tags."
                    }
                ]
            }
        ]
    )

    sub_topics = []
    for topic in re.findall(r"<sub_topic>.*</sub_topic>", message.content[0].text):
        sub_topics.append(topic[11:-12])

    return sub_topics


def detect_main_topic_selection(user_info, main_topics_response, user_response, main_topics):
    message = client.messages.create(
        model = model,
        max_tokens = 1000,
        temperature = 0,
        system = f"You are a professor who teaches elementary {user_info['language']}.",
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"My name is {user_info['name']}. Can you list the essential main topics for the elementary level of {user_info['language']}."
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": f"I am happy to meet you {user_info['name']}.\n{main_topics_response}"
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f'{user_response}\nGive me only the exact one topic name within <topic> tags. Do not explain anything further.'
                    }
                ]
            }
        ]
    )

    try:
        response = message.content[0].text
        response_search = re.search(r'<topic>.*</topic>', response)
        selected_topic = response_search.group(0)[7:-8]
        for topic in main_topics:
            if selected_topic == topic:
                return topic
        for topic in main_topics:
            if selected_topic in topic:
                return topic
    except:
        return None


def sub_topic_selection(user_info, sub_topics_response, user_response, main_topic, sub_topics):
    message = client.messages.create(
        model = model,
        max_tokens = 1000,
        temperature = 0,
        system = f"You are a professor who teaches elementary {user_info['language']}. The main topic on today's lesson is {main_topic}",
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"My name is {user_info['name']}. Can you list the essential sub topics for the elementary level of {user_info['language']} in the topic of {main_topic}"
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": f"I am happy to meet you {user_info['name']}.\n{sub_topics_response}"
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f'{user_response}\nGive me only the exact one sub topic name within <sub_topic> tags. Do not explain anything further.'
                    }
                ]
            }
        ]
    )

    try:
        response = message.content[0].text
        response_search = re.search(r'<sub_topic>.*</sub_topic>', response)
        selected_topic = response_search.group(0)[11:-12]
        for topic in sub_topics:
            if selected_topic == topic:
                return topic
        for topic in sub_topics:
            if selected_topic in topic:
                return topic
    except:
        return None


def organizer_by_state(state=0):

    if state == 0:
        state_machine = {
            "state": 0,
            "user_info": {
                "name": None,
                "language": None
            },
            "main_topics": None,
            "main_topic": None,
            "sub_topics": None,
            "sub_topic": None,
            "learning_objectives": {},
            "teachings": {}
        }

        intention_history = None
    else:
        with open(f'state_machine_{state}.json', 'r') as f:
            state_machine = json.load(f)
        with open(f'intention_history_{state}.json', 'r') as f:
            intention_history = json.load(f)

    while True:
        if state_machine["state"] == 0:
            with open("state_machine_0.json", "w") as f:
                json.dump(state_machine, f, indent=4)
            with open("intention_history_0.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            intention_history, user_info = greeting()
            state_machine["state"] = 1
            state_machine["user_info"] = user_info
            user_response = input()

            intention_history.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_response
                    }
                ]
            })
        elif state_machine["state"] == 1:
            with open("state_machine_1.json", "w") as f:
                json.dump(state_machine, f, indent=4)
            with open("intention_history_1.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            main_topics = None
            while True:
                intention = detect_user_intention(intention_history)
                if intention == intentions[0] or intention == intentions[2]:
                    main_topics = main_topics_section(state_machine['user_info'])
                elif intention == intentions[1]:
                    print("I understand you want to quit the lesson here. See you next time!")
                    return
                elif intention == intentions[3]:
                    print("I understand you want to see some sub topics but let me first introduce the main topics here.")
                    main_topics = main_topics_section(state_machine['user_info'])
                elif intention == intentions[4]:
                    print("I think there is some confusion. I think you want to quit a quiz but we didn't started the quiz yet. So let's start with the main topics.")
                    main_topics = main_topics_section(state_machine['user_info'])
                elif intention == intentions[5]:
                    print("I think you want to end the lesson that we didn't started yet. Do you want to quit the whole course?")
                    user_response = input()
                    intention_history.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": "I think you want to end the lesson that we didn't started yet. Do you want to quit the whole course?"
                            }
                        ]
                    })
                    intention_history.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    })
                    # intention = detect_user_intention(intention_history)
                elif intention == intentions[6]:
                    print("I think you want to start a quiz but we didn't even started the lesson yet. So, we can start with the main topics first.")
                    main_topics = main_topics_section(state_machine['user_info'])
                if main_topics is not None:
                    state_machine['state'] = 2
                    state_machine['main_topics'] = main_topics
                    break

            sub_topics = {}
            for topic in main_topics:
                sub_topics[topic] = None
            state_machine['sub_topics'] = sub_topics

        elif state_machine["state"] == 2:
            with open("state_machine_2.json", "w") as f:
                json.dump(state_machine, f, indent=4)
            with open("intention_history_2.json", "w") as f:
                json.dump(intention_history, f, indent=4)

            main_topics_response = f"For the {state_machine['user_info']['language']} Language, main topics are:"
            for t, topic in enumerate(state_machine['main_topics']):
                main_topics_response += f"\n\t{t+1}. {topic}"
            main_topics_response += "\nWhich topic would you like to start with?"
            print(main_topics_response)

            user_response = input()
            intention_history.append({
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": main_topics_response
                    }
                ]
            })
            intention_history.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_response
                    }
                ]
            })

            main_topic = None
            while True:
                intention = detect_user_intention(intention_history)
                print('your intention', intention)
                if intention == intentions[0] or intention == intentions[3]:
                    main_topic = detect_main_topic_selection(state_machine['user_info'], main_topics_response, user_response,
                                                             state_machine['main_topics'])
                    if main_topic is None:
                        bot_response = "I couldn't understand which main topic you want to pursue, can you please select a main topic?"
                        print(bot_response)
                        user_response = input()
                        intention_history.append({
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": bot_response
                                }
                            ]
                        })
                        intention_history.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": user_response
                                }
                            ]
                        })
                elif intention == intentions[1]:
                    print("See you later!")
                    return
                elif intention == intentions[2]:
                    print("Let's look at the main topics again.")
                    print(main_topics_response)
                    user_response = input()
                    intention_history[-1] = {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    }
                elif intention == intentions[4]:
                    print("You were not in the quiz. Can you select a topic please to further?")
                    user_response = input()
                    intention_history[-1] = {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    }
                elif intention == intentions[5]:
                    print("I understand you want to exit the lesson. But, we didn't start the lesson yet. Do you want to quit the whole course?")
                    user_response = input()
                    intention_history.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": "I think you want to end the lesson that we didn't started yet. Do you want to quit the whole course?"
                            }
                        ]
                    })
                    intention_history.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    })
                elif intention == intentions[6]:
                    print("I understand you want to proceed the quiz but you didn't select the sub topic yet. To continue, can you select a main topic please.")
                    user_response = input()
                    intention_history[-1] = {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    }
                if main_topic is not None:
                    state_machine['state'] = 3
                    state_machine['main_topic'] = main_topic
                    break

        elif state_machine['state'] == 3:
            with open("state_machine_3.json", "w") as f:
                json.dump(state_machine, f, indent=4)
            with open("intention_history_3.json", "w") as f:
                json.dump(intention_history, f, indent=4)

            if state_machine['sub_topics'][state_machine['main_topic']] is None:
                state_machine['sub_topics'][state_machine['main_topic']] = sub_topics_definition(state_machine['user_info'], state_machine['main_topic'])
            state_machine['state'] = 4

        elif state_machine['state'] == 4:
            with open("state_machine_4.json", "w") as f:
                json.dump(state_machine, f, indent=4)
            with open("intention_history_4.json", "w") as f:
                json.dump(intention_history, f, indent=4)

            sub_topics_response = f"For the {state_machine['user_info']['language']} Language, the sub topics for the {state_machine['main_topic']}:"
            for t, topic in enumerate(state_machine['sub_topics'][state_machine['main_topic']]):
                sub_topics_response += f"\n\t{t+1}. {topic}"
            sub_topics_response += "\nWhich sub topic would you like to study?"
            print(sub_topics_response)
            user_response = input()
            intention_history.append({
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": sub_topics_response
                    }
                ]
            })
            intention_history.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_response
                    }
                ]
            })

            sub_topic = None
            while True:
                intention = detect_user_intention(intention_history)
                print('your intention', intention)
                if intention == intentions[0]:
                    sub_topic = sub_topic_selection(state_machine['user_info'], sub_topics_response, user_response, state_machine['main_topic'], state_machine['sub_topics'][state_machine['main_topic']])

                    if sub_topic is None:
                        bot_response = "I couldn't understand which sub topic you want to pursue, can you please select a sub topic?"
                        print(bot_response)
                        user_response = input()
                        intention_history.append({
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": bot_response
                                }
                            ]
                        })
                        intention_history.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": user_response
                                }
                            ]
                        })
                elif intention == intentions[1]:
                    print("See you later!")
                    return
                elif intention == intentions[2]:
                    print("Let's look at the main topics again.")
                    state_machine['state'] = 2
                    state_machine['main_topic'] = None
                    break
                elif intention == intentions[3]:
                    print("You are already in the sub topic selection section. Can you select a sub topic please?")
                    user_response = input()
                    intention_history[-1] = {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    }
                elif intention == intentions[4]:
                    print("You were not in the quiz. Can you select a sub topic please to further?")
                    user_response = input()
                    intention_history[-1] = {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    }
                elif intention == intentions[5]:
                    print("I understand you want to exit the lesson. But, we didn't start the lesson yet. Do you want to quit the whole course?")
                    user_response = input()
                    intention_history.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": "I think you want to end the lesson that we didn't started yet. Do you want to quit the whole course?"
                            }
                        ]
                    })
                    intention_history.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    })
                elif intention == intentions[6]:
                    print("I understand you want to proceed the quiz but you didn't select the sub topic yet. To continue, can you select a sub topic please.")
                    user_response = input()
                    intention_history[-1] = {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    }
                if sub_topic is not None:
                    state_machine['state'] = 5
                    state_machine['sub_topic'] = sub_topic
                    break

        elif state_machine['state'] == 5:
            with open("state_machine_5.json", "w") as f:
                json.dump(state_machine, f, indent=4)
            with open("intention_history_5.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            print('sub topic you selected is:', state_machine['sub_topic'])

            learning_objectives = None
            heading = f"{state_machine['main_topic']}</>{state_machine['sub_topic']}"
            if "learning_objectives" in state_machine:
                if heading in state_machine['learning_objectives']:
                    learning_objectives = state_machine['learning_objectives'][heading]
            else:
                state_machine['learning_objectives'] = {}

            if learning_objectives is None:
                state_machine['learning_objectives'][heading] = learning_objectives_definition(state_machine['user_info'], state_machine['sub_topic'], state_machine['main_topic'])

            state_machine['state'] = 6

        elif state_machine['state'] == 6:
            with open("state_machine_6.json", "w") as f:
                json.dump(state_machine, f, indent=4)
            with open("intention_history_6.json", "w") as f:
                json.dump(intention_history, f, indent=4)

            if "teachings" not in state_machine:
                state_machine['teachings'] = {}

            heading = f"{state_machine['main_topic']}</>{state_machine['sub_topic']}"

            if heading in state_machine['teachings']:
                teaching = state_machine['teachings'][heading]
            else:
                teaching = None

            for learning_objective in state_machine['learning_objectives'][heading]:
                if learning_objective['state'] == "not_known":
                    objective = learning_objective['objective']
                    print(f"Current objective is:\n{objective}")

                    teaching = teach_learning_objective(state_machine['user_info'], state_machine['sub_topic'], state_machine['main_topic'], objective, teaching)
                    state_machine['teachings'][heading] = teaching
                    print("-------")
                    print(teaching[-1]['content'][0]['text'])
                    print("-------")
                    learning_objective['state'] = "taught"
                    state_machine['state'] = 7
                    break

            state_machine['state'] = 7

        elif state_machine['state'] == 7:
            with open("state_machine_7.json", "w") as f:
                json.dump(state_machine, f, indent=4)
            with open("intention_history_7.json", "w") as f:
                json.dump(intention_history, f, indent=4)

            print("Will be implemented soon!!!!")
            # TODO user intentioni algilanacak ama kurs icin farkli bir intention detection yazilabilir
            # TODO daha sonrasinda question varsa cevaplanacak, yoksa state 6 ile devam edilecek
            return


def teach_learning_objective(user_info, sub_topic, main_topic, learning_objective, teaching):
    if teaching is None:
        user_prompt = f"Hello, my name is {user_info['name']}. Give me regarding class helping to acquire the learning objective \"{learning_objective}\" in the {sub_topic} topic. Describe it in English!"

        teaching = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt
                    }
                ]
            }
        ]

    else:
        user_prompt = f"Give me regarding class helping to acquire the learning objective \"{learning_objective}\" in the {sub_topic} topic. Describe it in English!"

        teaching.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_prompt
                }
            ]
        })

    message = client.messages.create(
        model=model,
        max_tokens=1000,
        temperature=0,
        system=f"You are a professor who teaches elementary {user_info['language']} for foreign students, you speak English. Today's topic is {sub_topic} on the {main_topic} chapter, and the learning objective is ```{learning_objective}```. Do not ask any question to the student!",
        messages=teaching
    )

    teacher_text = message.content[0].text
    teacher_text += "\nDo you have any question or do you want me to continue?"
    teaching.append({
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": teacher_text
            }
        ]
    })

    return teaching


def learning_objectives_definition(user_info, sub_topic, main_topic):
    user_prompt = f"Define the core learning objectives of the {sub_topic} topic. The learning objective should only be correlated with the {sub_topic} topic but not coincide with others. List each related objective in between <objective> tags."

    message = client.messages.create(
        model = model,
        max_tokens = 1000,
        temperature = 0,
        system = f"You are a professor who teaches elementary {user_info['language']}, you speak English. Today's topic is {sub_topic} on the {main_topic} chapter.",
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt
                    }
                ]
            }
        ]
    )

    objectives = []
    for objective in re.findall(r"<objective>.*</objective>", message.content[0].text):
        objectives.append({"objective": objective[11:-12], "state": "not_known"})

    return objectives



# intentions = ["proceed", "quit", "go_to_main_topics", "go_to_sub_topics", "exit_quiz", "exit_lesson", "proceed_to_quiz"]

if __name__ == '__main__':

    API_KEY = os.getenv("API_KEY")
    if API_KEY is None:
        if os.path.exists("api_key.txt"):
            with open("api_key.txt", "r") as f:
                API_KEY = f.read().strip()
    
    if API_KEY is None:
        print("No API key found. Please provide an API key or create an api_key.txt file in the same directory.")
    else:
        model = "claude-3-haiku-20240307"
        # model = "claude-3-5-haiku-20241022"
        # model = "claude-3-5-sonnet-latest"
        intentions = ["proceed", "quit", "go_to_main_topics", "go_to_sub_topics", "exit_quiz", "exit_lesson", "proceed_to_quiz"]
        # TODO: change user info intention

        client = anthropic.Anthropic(api_key=API_KEY)
        organizer_by_state(state=0)

    # TODO -> intentionlara irrelevant eklenebilir, kullanici cok alakasiz bir sey soylediyse, bot 'anlamadim tekrar soyler misin' gibi bi sey diyebilir
    