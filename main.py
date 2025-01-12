import anthropic
import re
import json
import os
import random
from uuid import uuid4
import jsonpickle


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


def greeting(conversation):

    system_message = "Hello there, I will be guiding you to learn any language you want in beginner level. Can you briefly mention about yourself and which language do you want to learn?"
    conversation.append({
        "role": 'system',
        "message": system_message
    })
    print(system_message)

    user_response = input()
    conversation.append({
        "role": 'user',
        "message": user_response
    })
    name, language = detect_name_and_language(user_response)

    while name is None or language is None:
        if name is None and language is None:
            system_message = "Sorry, I didn't get your name and the language you're interested in. Can you provide these information?"
            conversation.append({
                "role": 'system',
                "message": system_message
            })
            print(system_message)
            user_response = input()
            conversation.append({
                "role": 'user',
                "message": user_response
            })
            name, language = detect_name_and_language(user_response)
        elif name is None:
            system_message = "Sorry, I didn't get your name. Can you provide me your name, so I can speak with you more freely"
            conversation.append({
                "role": 'system',
                "message": system_message
            })
            print(system_message)
            user_response = input()
            conversation.append({
                "role": 'user',
                "message": user_response
            })
            name, _ = detect_name_and_language(user_response)
        elif language is None:
            system_message = "Sorry, I didn't get the language you're interested in. To provide you the required language education, I need this information. What language do you want to learn?"
            conversation.append({
                "role": 'system',
                "message": system_message
            })
            print(system_message)
            user_response = input()
            conversation.append({
                "role": 'user',
                "message": user_response
            })
            _, language = detect_name_and_language(user_response)

    system_message = f"I am happy to meet you {name}\nLet's begin our {language} learning journey, shall we?"
    conversation.append({
        "role": 'system',
        "message": system_message
    })
    print(system_message)
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
    return intention_history, user_info, conversation


def relevant_check(history):

    if not relevant_check_enabled:
        return True

    tool_definition = {
        "name": "language_lecture_planner",
        "description": "The user is in a language teaching portal. The language lecture planner takes the is_relevant parameter and arranges the next step accordingly. is_relevant"
                       "parameter describes whether the user's response is directly connected and related to the language lecture content or not. If the user wants to learn something, but if "
                       "it is not connected to the previously mentioned topics, the is_relevant parameter should be False. But, if the user asks or makes a comment about something that is"
                       "strictly connected to the language lecture, then the is_relevant parameter should be True.\n"
                       "Even if the user response is somehow correlated with the language learning lecture, but if it is not a completely fit to the context, then the is_relevant"
                       " parameter should be False. The cohesion is the key point.",
        "input_schema": {
            "type": "object",
            "properties": {
                "is_relevant": {
                    "type": "boolean",
                    "description": "Is the user's response is directly relevant to the course content?"
                }
            },
            "required": ["is_relevant"]
        }
    }
    message = client.messages.create(
        model = model,
        max_tokens = 1000,
        temperature = 0,
        messages = history,
        tools = [tool_definition],
        tool_choice= {"type": "tool", "name": "language_lecture_planner"}
    )

    return message.content[0].input['is_relevant']


def detect_user_intention(intention_history):
    tool_definition = {
        "name": "intention_detector",
        "description": "Retrieve's the intention of the user which uses a portal to learn a language. The intention is one of <proceed>, <quit>, <go_to_main_topics>, <go_to_sub_topics>, <exit_quiz>, <exit_lesson>, <proceed_to_quiz>, <question>.\n"
                       "<proceed>: The user wants to go to the next step.\n"
                       "<quit>: The user wants to exit the portal.\n"
                       "<go_to_main_topics>: The user wants to go to the main topic selection step. There are main topics covering the basics of regarding language.\n"
                       "<go_to_sub_topics>: The user wants to go to the sub topic selection step. A sub topic is one part of the previously selected main topic.\n"
                       "<exit_quiz>: The user wants to end the quiz step, the reason might also be finishing the quiz.\n"
                       "<exit_lesson>: The user wants to end the lesson for the selected topic.\n"
                       "<proceed_to_quiz>: The user wants to go to the quiz step.\n"
                       "<question>: The user asks a question to get educated more on some learning objective.",
        "input_schema": {
            "type": "object",
            "properties": {
                "intention": {
                    "type": "string",
                    "description": "The intention of the user. It should one of the tags: <proceed>, <quit>, <go_to_main_topics>, <go_to_sub_topics>, <exit_quiz>, <exit_lesson>, <proceed_to_quiz>, <question>."
                }
            },
            "required": ["intention"]
        }
    }
    for intention in intention_history:
        if intention["content"] is None or len(intention['content']) == 0 or intention['content'][0]['text'] is None or len(intention['content'][0]['text']) == 0:
            intention['content'] = [
                {
                    "type": "text",
                    "text": "<no response>"
                }
            ]
    message = client.messages.create(
        model = model,
        max_tokens = 1000,
        temperature = 0,
        messages = intention_history,
        tools = [tool_definition],
        tool_choice= {"type": "tool", "name": "intention_detector"}
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
            "current_learning_objective": None,
            "teachings": {},
            "quizzes": None
        }

        intention_history = None
        conversation = []
    else:
        with open(f'state_machine_{state}.json', 'r') as f:
            state_machine = json.load(f)
            conversation = state_machine['conversation']
        with open(f'intention_history_{state}.json', 'r') as f:
            intention_history = json.load(f)

    conversation_id = uuid4()
    print('conversation_id', conversation_id)

    while True:
        latest_state = 0
        if state_machine["state"] == 0:
            latest_state = 0
            with open("state_machine_0.json", "w") as f:
                state_machine['conversation'] = conversation
                json.dump(state_machine, f, indent=4)
            with open("intention_history_0.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            with open(f"conversations/{conversation_id}.json", "w") as f:
                json.dump({"conversation": conversation, "state_machine": state_machine, "intention_history": intention_history}, f, indent=4)
            intention_history, user_info, conversation = greeting(conversation)
            state_machine["state"] = 1
            state_machine["user_info"] = user_info
            user_response = input()
            conversation.append({
                "role": "user",
                "message": user_response
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

        elif state_machine["state"] == 1:
            latest_state = 1
            with open("state_machine_1.json", "w") as f:
                state_machine['conversation'] = conversation
                json.dump(state_machine, f, indent=4)
            with open("intention_history_1.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            with open(f"conversations/{conversation_id}.json", "w") as f:
                json.dump({"conversation": conversation, "state_machine": state_machine, "intention_history": intention_history}, f, indent=4)
            main_topics = None
            while True:
                intention = detect_user_intention(intention_history)
                if intention == intentions[0] or intention == intentions[2]:
                    main_topics = main_topics_section(state_machine['user_info'])
                elif intention == intentions[1]:
                    system_message = "I understand you want to quit the lesson here. See you next time!"
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    return conversation_id, conversation, state_machine, intention_history, latest_state
                elif intention == intentions[3]:
                    system_message = "I understand you want to see some sub topics but let me first introduce the main topics here."
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    main_topics = main_topics_section(state_machine['user_info'])
                elif intention == intentions[4]:
                    system_message = "I think there is some confusion. I think you want to quit a quiz but we didn't started the quiz yet. So let's start with the main topics."
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    main_topics = main_topics_section(state_machine['user_info'])
                elif intention == intentions[5]:
                    system_message = "I think you want to end the lesson that we didn't started yet. Do you want to quit the whole course?"
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
                    intention_history.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": system_message
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
                    system_message = "I think you want to start a quiz but we didn't even started the lesson yet. So, we can start with the main topics first."
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    main_topics = main_topics_section(state_machine['user_info'])
                # TODO question intention will be added
                else:
                    system_message = f"This intention is not covered yet: {intention}"
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
                    intention_history[-1] = {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    }
                if main_topics is not None:
                    state_machine['state'] = 2
                    state_machine['main_topics'] = main_topics
                    break

            sub_topics = {}
            for topic in main_topics:
                sub_topics[topic] = None
            state_machine['sub_topics'] = sub_topics

        elif state_machine["state"] == 2:
            latest_state = 2
            with open("state_machine_2.json", "w") as f:
                state_machine['conversation'] = conversation
                json.dump(state_machine, f, indent=4)
            with open("intention_history_2.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            with open(f"conversations/{conversation_id}.json", "w") as f:
                json.dump({"conversation": conversation, "state_machine": state_machine, "intention_history": intention_history}, f, indent=4)

            main_topics_response = f"For the {state_machine['user_info']['language']} Language, main topics are:"
            for t, topic in enumerate(state_machine['main_topics']):
                main_topics_response += f"\n\t{t+1}. {topic}"
            main_topics_response += "\nWhich topic would you like to start with?"
            conversation.append({
                "role": "system",
                "message": main_topics_response
            })
            print(main_topics_response)

            user_response = input()
            conversation.append({
                "role": "user",
                "message": user_response
            })
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
                if intention == intentions[0] or intention == intentions[3]:
                    main_topic = detect_main_topic_selection(state_machine['user_info'], main_topics_response, user_response,
                                                             state_machine['main_topics'])
                    if main_topic is None:
                        bot_response = "I couldn't understand which main topic you want to pursue, can you please select a main topic?"
                        conversation.append({
                            "role": "system",
                            "message": bot_response
                        })
                        print(bot_response)
                        user_response = input()
                        conversation.append({
                            "role": "user",
                            "message": user_response
                        })
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
                    system_message = "See you later!"
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    return conversation_id, conversation, state_machine, intention_history, latest_state
                elif intention == intentions[2]:
                    system_message = "Let's look at the main topics again."
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    conversation.append({
                        "role": "system",
                        "message": main_topics_response
                    })
                    print(main_topics_response)
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
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
                    system_message = "You were not in the quiz. Can you select a topic please to further?"
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
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
                    system_message = "I understand you want to exit the lesson. But, we didn't start the lesson yet. Do you want to quit the whole course?"
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
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
                    system_message = "I understand you want to proceed the quiz but you didn't select the sub topic yet. To continue, can you select a main topic please."
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
                    intention_history[-1] = {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    }
                else:
                    # TODO question intention will be added
                    system_message = f"This intention is not covered yet: {intention}"
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
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
            latest_state = 3
            with open("state_machine_3.json", "w") as f:
                state_machine['conversation'] = conversation
                json.dump(state_machine, f, indent=4)
            with open("intention_history_3.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            with open(f"conversations/{conversation_id}.json", "w") as f:
                json.dump({"conversation": conversation, "state_machine": state_machine, "intention_history": intention_history}, f, indent=4)

            if state_machine['sub_topics'][state_machine['main_topic']] is None:
                state_machine['sub_topics'][state_machine['main_topic']] = sub_topics_definition(state_machine['user_info'], state_machine['main_topic'])
            state_machine['state'] = 4

        elif state_machine['state'] == 4:
            latest_state = 4
            with open("state_machine_4.json", "w") as f:
                json.dump(state_machine, f, indent=4)
                state_machine['conversation'] = conversation
            with open("intention_history_4.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            with open(f"conversations/{conversation_id}.json", "w") as f:
                json.dump({"conversation": conversation, "state_machine": state_machine, "intention_history": intention_history}, f, indent=4)

            sub_topics_response = f"For the {state_machine['user_info']['language']} Language, the sub topics for the {state_machine['main_topic']}:"
            for t, topic in enumerate(state_machine['sub_topics'][state_machine['main_topic']]):
                sub_topics_response += f"\n\t{t+1}. {topic}"
            sub_topics_response += "\nWhich sub topic would you like to study?"
            conversation.append({
                "role": "system",
                "message": sub_topics_response
            })
            print(sub_topics_response)
            user_response = input()
            conversation.append({
                "role": "user",
                "message": user_response
            })
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
                if intention == intentions[0]:
                    sub_topic = sub_topic_selection(state_machine['user_info'], sub_topics_response, user_response, state_machine['main_topic'], state_machine['sub_topics'][state_machine['main_topic']])

                    if sub_topic is None:
                        bot_response = "I couldn't understand which sub topic you want to pursue, can you please select a sub topic?"
                        conversation.append({
                            "role": "system",
                            "message": bot_response
                        })
                        print(bot_response)
                        user_response = input()
                        conversation.append({
                            "role": "user",
                            "message": user_response
                        })
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
                    system_response = "See you later!"
                    conversation.append({
                        "role": "system",
                        "message": system_response
                    })
                    print(system_response)
                    return conversation_id, conversation, state_machine, intention_history, latest_state
                elif intention == intentions[2]:
                    system_message = "Let's look at the main topics again."
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    state_machine['state'] = 2
                    state_machine['main_topic'] = None
                    break
                elif intention == intentions[3]:
                    system_message = "You are already in the sub topic selection section. Can you select a sub topic please?"
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
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
                    system_message = "You were not in the quiz. Can you select a sub topic please to go further?"
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
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
                    system_message = "I understand you want to exit the lesson. But, we didn't start the lesson yet. Do you want to quit the whole course?"
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
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
                    system_message = "I understand you want to proceed the quiz but you didn't select the sub topic yet. To continue, can you select a sub topic please."
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
                    intention_history[-1] = {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    }
                else:
                    # TODO question intention will be captured
                    system_message = f"This intention is not covered yet: {intention}"
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
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
            latest_state = 5
            with open("state_machine_5.json", "w") as f:
                state_machine['conversation'] = conversation
                json.dump(state_machine, f, indent=4)
            with open("intention_history_5.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            with open(f"conversations/{conversation_id}.json", "w") as f:
                json.dump({"conversation": conversation, "state_machine": state_machine, "intention_history": intention_history}, f, indent=4)

            # system_message = 'sub topic you selected is:' + str(state_machine['sub_topic'])
            # conversation.append({
            #     "role": "system",
            #     "message": system_message
            # })
            # print(system_message)

            learning_objectives = None
            heading = f"{state_machine['main_topic']}</>{state_machine['sub_topic']}"
            if "learning_objectives" in state_machine:
                if heading in state_machine['learning_objectives']:
                    learning_objectives = state_machine['learning_objectives'][heading]
            else:
                state_machine['learning_objectives'] = {}

            if learning_objectives is None or len(learning_objectives) == 0:
                state_machine['learning_objectives'][heading] = learning_objectives_definition(state_machine['user_info'], state_machine['sub_topic'], state_machine['main_topic'])

            state_machine['state'] = 6

        elif state_machine['state'] == 6:
            latest_state = 6
            with open("state_machine_6.json", "w") as f:
                state_machine['conversation'] = conversation
                json.dump(state_machine, f, indent=4)
            with open("intention_history_6.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            with open(f"conversations/{conversation_id}.json", "w") as f:
                json.dump({"conversation": conversation, "state_machine": state_machine, "intention_history": intention_history}, f, indent=4)

            if "teachings" not in state_machine:
                state_machine['teachings'] = {}

            heading = f"{state_machine['main_topic']}</>{state_machine['sub_topic']}"

            if heading in state_machine['teachings']:
                teaching = state_machine['teachings'][heading]
            else:
                teaching = None

            taught = False
            for learning_objective in state_machine['learning_objectives'][heading]:
                if learning_objective['state'] == "not_known" or learning_objective['state'] == 'failed':
                    objective = learning_objective['objective']
                    state_machine['current_learning_objective'] = objective

                    failed_info = None
                    if learning_objective['state'] == 'failed':
                        quiz_text = prepare_quiz_sheet([learning_objective['quiz']])
                        pure_answer = learning_objective['pure_answer']
                        feedback_text = ""
                        for fb_index, fb in enumerate(learning_objective['feedback']):
                            feedback_text += f"{fb_index}-> {fb}\n"
                        failed_info = f"Also consider that I took a quiz for the same learning objective:\n{quiz_text}\nMy answers were:\n{pure_answer}\nAnd I received the following feedback:\n{feedback_text}. So, give me a comprehensive description with more details and help me to understand the points where I tackle the most."
                    teaching = teach_learning_objective(state_machine['user_info'], state_machine['sub_topic'], state_machine['main_topic'], objective, teaching, failed_info)
                    learning_objective['lesson'] += teaching[-2:]
                    state_machine['teachings'][heading] = teaching
                    conversation.append({
                        "role": "system",
                        "message": teaching[-1]['content'][0]['text']
                    })
                    print("-------")
                    print(teaching[-1]['content'][0]['text'])
                    print("-------")
                    learning_objective['state'] = "taught"
                    state_machine['state'] = 7
                    taught = True
                    break

            if not taught:
                state_machine['state'] = 8

        elif state_machine['state'] == 7:
            latest_state = 7
            with open("state_machine_7.json", "w") as f:
                state_machine['conversation'] = conversation
                json.dump(state_machine, f, indent=4)
            with open("intention_history_7.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            with open(f"conversations/{conversation_id}.json", "w") as f:
                json.dump({"conversation": conversation, "state_machine": state_machine, "intention_history": intention_history}, f, indent=4)

            user_response = input()
            conversation.append({
                "role": "user",
                "message": user_response
            })
            heading = f"{state_machine['main_topic']}</>{state_machine['sub_topic']}"
            teaching = state_machine['teachings'][heading]
            teaching.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_response
                    }
                ]
            })

            while True:
                # is_relevant = relevant_check(teaching)
                # print("is relevant:", is_relevant)
                intention = detect_user_intention(intention_history + teaching)
                # print("intention:", intention)
                if intention == intentions[0]:
                    state_machine['state'] = 6
                    for learning_objective in state_machine['learning_objectives'][heading]:
                        if learning_objective['objective'] == state_machine['current_learning_objective']:
                            learning_objective['state'] = 'taught'
                            state_machine['current_learning_objective'] = None
                            break
                    break
                elif intention == intentions[1]:
                    system_message = "See you later!"
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    return conversation_id, conversation, state_machine, intention_history, latest_state
                elif intention == intentions[2]:
                    system_message = "Let's look at the main topics again."
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    state_machine['state'] = 2
                    state_machine['main_topic'] = None
                    break
                elif intention == intentions[3]:
                    system_message = "Let's look at the sub topics again."
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    state_machine['state'] = 4
                    state_machine['sub_topic'] = None
                    break
                elif intention == intentions[4]:
                    system_message = "You were not in the quiz. You can ask questions related to the topics discussed or would you like me to continue?"
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
                    teaching[-1] = {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    }
                    continue
                elif intention == intentions[5]:
                    assistant_response = "I understand you want to exit the lesson. Do you want to quit, go to another lesson, or take a quiz?"
                    conversation.append({
                        "role": "system",
                        "message": assistant_response
                    })
                    print(assistant_response)
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
                    teaching.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": assistant_response
                            }
                        ]
                    })
                    teaching.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    })
                    continue
                elif intention == intentions[6]:
                    system_message = "I understand you want to take the quiz now!"
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    state_machine['state'] = 8
                    state_machine['teachings'][heading] = teaching
                    break
                elif intention == intentions[7]:
                    teaching, teacher_text = answer_question(state_machine['user_info'], state_machine['sub_topic'], state_machine['main_topic'], state_machine['current_learning_objective'], teaching)
                    conversation.append({
                        "role": "system",
                        "message": teacher_text
                    })
                    print(teacher_text)
                    state_machine['teachings'][heading] = teaching
                    for learning_objective in state_machine['learning_objectives'][heading]:
                        if learning_objective['objective'] == state_machine['current_learning_objective']:
                            learning_objective['lesson'] += teaching[-2:]
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
                    teaching.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    })
                    continue
                else:
                    system_message = f"this intention is not covered yet: {intention}"
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
                    teaching[-1] = {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    }
                    continue

        elif state_machine['state'] == 8:
            latest_state = 8
            with open("state_machine_8.json", "w") as f:
                state_machine['conversation'] = conversation
                json.dump(state_machine, f, indent=4)
            with open("intention_history_8.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            with open(f"conversations/{conversation_id}.json", "w") as f:
                json.dump({"conversation": conversation, "state_machine": state_machine, "intention_history": intention_history}, f, indent=4)

            heading = f"{state_machine['main_topic']}</>{state_machine['sub_topic']}"
            learning_objectives = state_machine['learning_objectives'][heading].copy()
            random.shuffle(learning_objectives)
            quizzes = []
            quiz_types = ["blank_space", "translate", "match"]
            random.shuffle(quiz_types)
            found_an_objective = False
            for learning_objective in learning_objectives:
                if learning_objective['state'] == 'taught' or learning_objective['state'] == 'failed':
                    found_an_objective = True
                    break
            if not found_an_objective:
                for learning_objective in learning_objectives:
                    learning_objective['state'] = 'taught'
            for l, learning_objective in enumerate(learning_objectives):
                if learning_objective['state'] == 'taught':
                    quiz = None
                    quiz_type = quiz_types[l]
                    if quiz_type == "blank_space":
                        quiz = prepare_quiz_blank_space(state_machine['user_info'], state_machine['main_topic'], state_machine['sub_topic'], learning_objective['objective'], learning_objective['lesson'])
                    elif quiz_type == "translate":
                        quiz = prepare_quiz_translate(state_machine['user_info'], state_machine['main_topic'], state_machine['sub_topic'], learning_objective['objective'], learning_objective['lesson'])
                    elif quiz_type == "match":
                        quiz = prepare_quiz_match(state_machine['user_info'], state_machine['main_topic'], state_machine['sub_topic'], learning_objective['objective'], learning_objective['lesson'])
                    quizzes.append({
                        "type": quiz_type,
                        "quiz": quiz,
                        "learning_objective": learning_objective
                    })
                elif learning_objective['state'] == 'failed':
                    quiz_text = prepare_quiz_sheet([learning_objective['quiz']])
                    pure_answer = learning_objective['pure_answer']
                    feedback_text = ""
                    for fb_index, fb in enumerate(learning_objective['feedback']):
                        feedback_text += f"{fb_index}-> {fb}\n"
                    prev_info = f"Also consider that I had another quiz earlier:\n{quiz_text}\nMy answers were:\n{pure_answer}\nAnd I received the following feedback:\n{feedback_text}Can you prepare the quiz so that it's not directly copy of my previous quiz and the new quiz assesses my knowledge better?"
                    quiz = None
                    quiz_type = quiz_types[l]
                    if quiz_type == "blank_space":
                        quiz = prepare_quiz_blank_space(state_machine['user_info'], state_machine['main_topic'], state_machine['sub_topic'], learning_objective['objective'], learning_objective['lesson'], prev_info)
                    elif quiz_type == "translate":
                        quiz = prepare_quiz_translate(state_machine['user_info'], state_machine['main_topic'], state_machine['sub_topic'], learning_objective['objective'], learning_objective['lesson'], prev_info)
                    elif quiz_type == "match":
                        quiz = prepare_quiz_match(state_machine['user_info'], state_machine['main_topic'], state_machine['sub_topic'], learning_objective['objective'], learning_objective['lesson'], prev_info)
                    quizzes.append({
                        "type": quiz_type,
                        "quiz": quiz,
                        "learning_objective": learning_objective
                    })

            state_machine['quizzes'] = quizzes
            state_machine['state'] = 9

        elif state_machine['state'] == 9:
            latest_state = 9
            with open("state_machine_9.json", "w") as f:
                state_machine['conversation'] = conversation
                json.dump(state_machine, f, indent=4)
            with open("intention_history_9.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            with open(f"conversations/{conversation_id}.json", "w") as f:
                json.dump({"conversation": conversation, "state_machine": state_machine, "intention_history": intention_history}, f, indent=4)

            quiz_sheet = prepare_quiz_sheet(state_machine['quizzes'])
            heading = f"{state_machine['main_topic']}</>{state_machine['sub_topic']}"
            look_up = prepare_look_up(quiz_sheet, state_machine['teachings'][heading], state_machine['user_info'], state_machine['main_topic'], state_machine['sub_topic'])
            quiz_sheet = look_up + quiz_sheet
            with open('quiz_sheet.txt', 'w') as f:
                f.write(quiz_sheet)
            system_message = "\nQUIZ SAVED TO quiz_sheet.txt\nPlease open it and complete the questions. When you save your changes on the same file, please type COMPLETED here"
            conversation.append({
                "role": "system",
                "message": system_message
            })
            conversation.append({
                "role": "quiz",
                "message": quiz_sheet
            })
            print(system_message)
            user_response = input()
            conversation.append({
                "role": "user",
                "message": user_response
            })
            if user_response == "COMPLETED":
                state_machine['state'] = 10
            else:
                # TODO intetion will be detected
                state_machine['state'] = 10
                # return

        elif state_machine['state'] == 10:
            latest_state = 10
            with open("state_machine_10.json", "w") as f:
                state_machine['conversation'] = conversation
                json.dump(state_machine, f, indent=4)
            with open("intention_history_10.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            with open(f"conversations/{conversation_id}.json", "w") as f:
                json.dump({"conversation": conversation, "state_machine": state_machine, "intention_history": intention_history}, f, indent=4)

            with open('quiz_sheet.txt', 'r') as f:
                quiz_sheet = f.read()
            conversation.append({
                "role": "quiz_answer",
                "message": quiz_sheet
            })
            answers, pure_answers = get_answers(quiz_sheet)
            sessions = []
            failed_objectives = []
            known_objectives = []
            heading = f"{state_machine['main_topic']}</>{state_machine['sub_topic']}"
            for i in range(len(state_machine['quizzes'])):
                quiz = state_machine['quizzes'][i]
                state_machine['quizzes'][i]['pure_answer'] = pure_answers[i]
                feedback, session = get_feedback(state_machine['user_info'], state_machine['main_topic'], state_machine['sub_topic'], quiz['learning_objective']['objective'], quiz, answers[i])
                total = 0
                correct = 0
                for fb in feedback:
                    total += 1
                    if fb['score']:
                        correct += 1
                for learning_objective in state_machine['learning_objectives'][heading]:
                    if learning_objective['objective'] == quiz['learning_objective']['objective']:
                        total = 10
                        if total != 0 and correct / total >= 0.7:
                            known_objectives.append(learning_objective['objective'])
                            learning_objective['state'] = "known"
                        else:
                            failed_objectives.append(learning_objective['objective'])
                            learning_objective['state'] = "failed"
                            learning_objective['quiz'] = quiz
                            learning_objective['feedback'] = feedback
                            learning_objective['pure_answer'] = quiz['pure_answer']
                        break

                system_message = f"\n\nFOR THE QUIZ {i+1}:\n{session[-1]['content'][0]['text']}"
                conversation.append({
                    "role": "system",
                    "message": system_message
                })
                print(system_message)
                sessions.extend(session)

            bot_response = ""
            if len(known_objectives) > 0:
                if len(known_objectives) == 1:
                    bot_response += "Well Done! You successfully learned the following objective:\n"
                else:
                    bot_response += "Well Done! You successfully learned the following objectives:\n"
                for objective in known_objectives:
                    bot_response += f"\t- {objective}\n"
            if len(failed_objectives) > 0:
                if len(failed_objectives) == 1:
                    bot_response += "Unfortunately, you failed to learn the following objective:\n"
                else:
                    bot_response += "Unfortunately, you failed to learn the following objectives:\n"
                for objective in failed_objectives:
                    bot_response += f"\t- {objective}\n"
                bot_response += "Do you want to retake the current lesson?"
            else:
                bot_response += "Do you want to take another lesson?"

            conversation.append({
                "role": "system",
                "message": bot_response
            })
            print(bot_response)
            sessions[-1]['content'][0]['text'] += bot_response

            user_response = input()
            conversation.append({
                "role": "user",
                "message": user_response
            })
            sessions.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_response
                    }
                ]
            })

            while True:
                # is_relevant = relevant_check(sessions)
                # print("is relevant:", is_relevant)
                intention = detect_user_intention(sessions)
                # print("intention:", intention)

                # proceed
                if intention == intentions[0]:
                    if len(failed_objectives) > 0:
                        system_message = "Let's study the lesson again."
                        conversation.append({
                            "role": "system",
                            "message": system_message
                        })
                        print(system_message)
                        state_machine['state'] = 6
                    else:
                        system_message = "Let's look at the main topics again."
                        conversation.append({
                            "role": "system",
                            "message": system_message
                        })
                        print(system_message)
                        state_machine['state'] = 2
                    break
                # quit
                elif intention == intentions[1]:
                    system_message = "See you later!"
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    return conversation_id, conversation, state_machine, intention_history, latest_state
                # go_to_main_topics
                elif intention == intentions[2]:
                    system_message = "Let's look at the main topics again."
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    state_machine['state'] = 2
                    break
                # go_to_sub_topics
                elif intention == intentions[3]:
                    system_message = "Let's look at the sub topics again."
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    state_machine['state'] = 4
                    break
                # exit_quiz
                elif intention == intentions[4]:
                    bot_response = "You already finished the quiz, do you want to proceed?"
                    sessions.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": bot_response
                            }
                        ]
                    })
                    conversation.append({
                        "role": "system",
                        "message": bot_response
                    })
                    print(bot_response)
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
                    sessions.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    })
                    continue
                # exit lesson
                elif intention == intentions[5]:
                    bot_response = "Current lesson already finished, do you want to quit?"
                    sessions.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": bot_response
                            }
                        ]
                    })
                    conversation.append({
                        "role": "system",
                        "message": bot_response
                    })
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
                    sessions.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    })
                    continue
                # proceed to quiz
                elif intention == intentions[6]:
                    system_message = "I understand you want to retake the quiz."
                    conversation.append({
                        "role": "system",
                        "message": system_message
                    })
                    print(system_message)
                    state_machine['state'] = 8
                    break
                # question
                elif intention == intentions[7]:
                    bot_response = "Before answering your question, I need to know how would like you continue?"
                    conversation.append({
                        "role": "system",
                        "message": bot_response
                    })
                    print(bot_response)
                    sessions.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": bot_response
                            }
                        ]
                    })
                    user_response = input()
                    conversation.append({
                        "role": "user",
                        "message": user_response
                    })
                    sessions.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_response
                            }
                        ]
                    })
                    continue

        # elif state_machine['state'] == 11:
        #     with open("state_machine_11.json", "w") as f:
        #         state_machine['conversation'] = conversation
        #         json.dump(state_machine, f, indent=4)
        #     with open("intention_history_11.json", "w") as f:
        #         json.dump(intention_history, f, indent=4)
        #     with open(f"conversations/{conversation_id}.json", "w") as f:
        #         json.dump({"conversation": conversation, "state_machine": state_machine, "intention_history": intention_history}, f, indent=4)
        #     state_machine['state'] = 6

        else:

            with open("state_machine_latest.json", "w") as f:
                state_machine['conversation'] = conversation
                json.dump(state_machine, f, indent=4)
            with open("intention_history_latest.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            print(f"This state is not implemented yet: State {state_machine['state']}")
            return conversation_id, conversation, state_machine, intention_history, latest_state

        try:
            with open("intention_history_latest.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            state_machine['conversation'] = conversation
            state_machine_data = jsonpickle.encode(state_machine, unpicklable=False)
            with open("state_machine_latest.json", "w") as f:
                f.write(state_machine_data)
            with open(f"conversations/{conversation_id}.json", "w") as f:
                json.dump({"conversation": conversation, "state_machine": state_machine, "intention_history": intention_history}, f, indent=4)
        except:
            with open(f'state_machine_{latest_state}.json', 'r') as f:
                state_machine = json.load(f)
                conversation = state_machine['conversation']
            with open(f'intention_history_{latest_state}.json', 'r') as f:
                intention_history = json.load(f)
            with open("intention_history_latest.json", "w") as f:
                json.dump(intention_history, f, indent=4)
            state_machine['conversation'] = conversation
            state_machine_data = jsonpickle.encode(state_machine, unpicklable=False)
            with open("state_machine_latest.json", "w") as f:
                f.write(state_machine_data)
            with open(f"conversations/{conversation_id}.json", "w") as f:
                json.dump({"conversation": conversation, "state_machine": state_machine, "intention_history": intention_history}, f, indent=4)


# intentions = ["proceed", "quit", "go_to_main_topics", "go_to_sub_topics", "exit_quiz", "exit_lesson", "proceed_to_quiz", "question"]


def get_feedback(user_info, main_topic, sub_topic, learning_objective, quiz, answers):
    user_message = (f"I solved a quiz and want you to evaluate my answers. Each question is between <question> tags and inside there is a real answer in between <answer> tags and my response in between <response> tags.\n"
                    f"For instance example question looks like this:\n"
                    f"<question>Example question is in here <answer>predefined answer is in here</answer><response>my response is in here<response></question>\n\n"
                    f"Before this quiz, I took a lecture and here it is:\n")
    for part in quiz['learning_objective']['lesson']:
        if part['role'] == "user":
            tag = "Student"
        else:
            tag = "Teacher"
        current_line = f"<{tag}>{part['content'][0]['text']}</{tag}>"
        user_message += "\n" + current_line

    if quiz['type'] == "translate":
        user_message += "\n\nFor the given lecture, I solved a translation quiz. The quiz expects to translate the phrases to the target language. The phrases are in between ||-> <-|| symbols. The quiz is here:"
    elif quiz['type'] == "match":
        user_message += "\n\nFor the given lecture, I solved a matching quiz. For each English phrase, I needed to select the correct target language phrase. The quiz is here:"
    elif quiz['type'] == "blank_space":
        user_message += "\n\nFor the given lecture, I solved a blank space quiz. For each blank space shown with '___' symbols, I needed to write the correct phrase. The quiz is here:"
    for answer, question in zip(answers, quiz['quiz']):
        if quiz['type'] == "translate":
            user_message += "\n<question>" + question['sentence'] + "<answer>" + question['answer'] + "</answer>" + "<response>" + answer + "</response>" + "</question>"
        elif quiz['type'] == "match":
            current_answer = None
            for q in quiz['quiz']:
                if q['char'] == answer:
                    current_answer = q['tar']
                    break

            user_message += "\n<question>" + question['eng'] + "<answer>" + question['tar'] + "</answer>" + "<response>"
            if current_answer is not None:
                user_message += current_answer
            user_message += "</response>" + "</question>"

        elif quiz['type'] == "blank_space":
            user_message += "\n<question>" + question['sentence'] + "<answer>" + question['answer'] + "</answer>" + "<response>" + answer + "</response>" + "</question>"

    user_message += "For each question give me an evaluation in between <eval> tags. This evaluation should include <true> or <false> label and an explanation why the response is correct or not."

    message = client.messages.create(
        model=model,
        max_tokens=1000,
        temperature=0,
        system=f"You are a professor who teaches elementary {user_info['language']}. Today's topic is {sub_topic} on the {main_topic} chapter, and the learning objective is ```{learning_objective}```. You need to evaluate the students capabilities regarding the given quiz and give feedback.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_message
                    }
                ]
            }
        ]
    )

    feedback = []
    evaluations = message.content[0].text
    for evaluation in re.findall(r"<eval>.*?</eval>", evaluations, re.DOTALL):
        evaluation = evaluation[6:-7]
        score_search = re.search("<true>", evaluation)
        if score_search is not None:
            score = True
            evaluation = evaluation[:score_search.span(0)[0]] + evaluation[score_search.span(0)[1]:]
        else:
            score = False
            score_search = re.search("<false>", evaluation)
            if score_search is not None:
                evaluation = evaluation[:score_search.span(0)[0]] + evaluation[score_search.span(0)[1]:]
        feedback.append({
            "score": score,
            "evaluation": evaluation
        })

    teacher_message = ""
    for i, feed in enumerate(feedback):
        teacher_message += f"{i+1}-> Your answer is "
        if feed['score']:
            teacher_message += "CORRECT\n"
        else:
            teacher_message += "WRONG\n"
        teacher_message += f"{feed['evaluation']}\n"

    quiz_session = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_message
                }
            ]
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": teacher_message
                }
            ]
        }
    ]
    return feedback, quiz_session


def get_answers(quiz_sheet):
    answers = []
    pure_answers = []
    quiz_sheet = quiz_sheet.replace("======ANSWER=====", "answer", 1)
    for answer in re.findall(r"======ANSWER=====.*?======ANSWER=====", quiz_sheet, re.DOTALL):
        pure_answers.append(answer[17:-18])
        answer = answer[17:-18] + "11->"
        current_answers = []
        for i in range(1, 11):
            answer_search = re.search(rf"{i}->.*?\n{i+1}->", answer, re.DOTALL)
            answer_search = answer_search.group(0)[len(f"{i}->"):-len(f"{i+1}->")].strip()
            current_answers.append(answer_search)
        answers.append(current_answers)
    return answers, pure_answers


def prepare_look_up(quiz_sheet, lesson, user_info, main_topic, sub_topic):
    look_up = "Here are some important lecture notes that you might use in the quiz.\n"

    user_message = (f"I have a quiz:\n<quiz>{quiz_sheet}</quiz>.\n"
                    f"And here is the complete lecture I received:\n")
    for part in lesson:
        if part['role'] == "user":
            tag = "Student"
        else:
            tag = "Teacher"
        current_line = f"<{tag}>{part['content'][0]['text']}</{tag}>"
        user_message += "\n" + current_line

    user_message += "\n\nCan you prepare me a short look up table which consists of only the base necessary information in a distilled format in between <look_up> tags?"

    message = client.messages.create(
        model=model,
        max_tokens=1000,
        temperature=0,
        system=f"You are a professor who teaches elementary {user_info['language']}. Today's topic is {sub_topic} on the {main_topic} chapter. You need to prepare a look up table to help students to receive required information to be used in the quiz considering the given lecture.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_message
                    }
                ]
            }
        ]
    )
    response = message.content[0].text

    response_search = re.search(r"<look_up>.*?</look_up>", response, re.DOTALL)
    if response_search is None:
        return None
    look_up += response_search.group(0)[9:-10] + "\n\n"
    return look_up


def prepare_quiz_sheet(quizzes):
    quiz_text = "\n\nIMPORTANT NOTE: Please do not change the type of the document. Only write your answers to the according answer sheet in between ======ANSWER===== decorators.\n\n"

    for quiz in quizzes:
        if quiz['type'] == "blank_space":
            quiz_text += "FILL IN THE BLANK SPACES IN THE BELOW SENTENCES\n"
            for q, question in enumerate(quiz['quiz']):
                quiz_text += f"{q + 1}-> {question['sentence']}\n"
        elif quiz['type'] == "translate":
            quiz_text += "TRANSLATE THE PHRASES POINTED WITHIN ||-> <-|| SYMBOLS\n"
            for q, question in enumerate(quiz['quiz']):
                quiz_text += f"{q + 1}-> {question['sentence']}\n"
        elif quiz['type'] == "match":
            quiz_text += "MATCH THE PHRASES, WRITE ONLY THE CHARACTER (for instance, 1-> c  2-> d)\n"
            for q, question in enumerate(quiz['quiz']):
                quiz_text += f"{q + 1}-> {question['eng']}\n"
            quiz_text += "\n"
            for q, question in enumerate(sorted(quiz['quiz'], key=lambda x:x["char"])):
                quiz_text += f"{question['char']}-> {question['tar']}\n"
        quiz_text += "\n======ANSWER=====\n"
        for q, question in enumerate(quiz['quiz']):
            quiz_text += f"{q + 1}-> \n"
        quiz_text += "\n======ANSWER=====\n\n\n"

    return quiz_text


def prepare_quiz_match(user_info, main_topic, sub_topic, learning_objective, teaching, prev_info=None):
    user_message = (f"Prepare me 10 questions as a matching quiz. Each question should be in between <question> tags. Each question will be consisting of a pair. There should be English phrase and it's regarding pair will be {user_info['language']}. "
                    f"Each pair should be related with the discussed learning objective in the lecture. Each question should include a <eng> tags including the English part of the pair and <target> tags including the target language part of the pair.\n"
                    f"For instance, a question structure can be like the following:\n"
                    f"<question><eng>English sentence or a phrase in here</eng><target>{user_info['language']} sentence or a phrase in here</target></question>\n"
                    f"\n"
                    f"The questions should be related to the material discussed in the lecture. Consider that learning objective is '{learning_objective}'. Prepare beginner level questions and only ask what is taught in the lecture.\n"
                    f"The lecture:")
    if prev_info is not None:
        user_message += f"\n{prev_info}"
    for part in teaching:
        if part['role'] == "user":
            tag = "Student"
        else:
            tag = "Teacher"
        current_line = f"<{tag}>{part['content'][0]['text']}</{tag}>"
        user_message += "\n" + current_line

    user_message += "\n\nGive me the questions."

    message = client.messages.create(
        model=model,
        max_tokens=1000,
        temperature=0,
        system=f"You are a professor who teaches elementary {user_info['language']}. Today's topic is {sub_topic} on the {main_topic} chapter, and the learning objective is ```{learning_objective}```. You need to prepare a quiz assessing the students capabilities regarding the given lecture.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_message
                    }
                ]
            }
        ]
    )
    quiz = message.content[0].text
    structured_quiz = []
    chars = ['a','b','c','d','e','f','g','h','i','j']
    random.shuffle(chars)
    for q, question in enumerate(re.findall(r"<question>.*?</question>", quiz, re.DOTALL)):
        eng_search = re.search(r"<eng>.*?</eng>", question, re.DOTALL)
        if eng_search is None:
            continue
        tar_search = re.search(r"<target>.*?</target>", question, re.DOTALL)
        if tar_search is None:
            continue
        structured_quiz.append({
            "eng": eng_search.group(0)[5:-6].strip(),
            "tar": tar_search.group(0)[8:-9].strip(),
            "number": str(q),
            "char": chars[q]
        })
    return structured_quiz


def prepare_quiz_translate(user_info, main_topic, sub_topic, learning_objective, teaching, prev_info=None):
    user_message = (f"Prepare me 10 questions as a translation quiz. Each question should be in between <question> tags. Each question will be a {user_info['language']} sentence "
                    f"related to the discussed learning objective. Each question should include a portion in between <translate> tags and the student will be asked to translate these phrases to English. Give the correct translation answer in between <answer> tags which is also inside the question tags.\n"
                    f"For instance, a question structure can be like the following:\n"
                    f"<question>{user_info['language']} sentence related to the lecture and <translate> some portion of the sentence </translate> will be predicted by the student <answer>correct translation of the selected portion</answer></question>\n"
                    f"\n"
                    f"The questions should be related to the material discussed in the lecture. Consider that learning objective is '{learning_objective}'. Prepare beginner level questions and only ask what is taught in the lecture.\n"
                    f"The lecture:")
    if prev_info is not None:
        user_message += f"\n{prev_info}"
    for part in teaching:
        if part['role'] == "user":
            tag = "Student"
        else:
            tag = "Teacher"
        current_line = f"<{tag}>{part['content'][0]['text']}</{tag}>"
        user_message += "\n" + current_line

    user_message += "\n\nGive me the questions."

    message = client.messages.create(
        model=model,
        max_tokens=1000,
        temperature=0,
        system=f"You are a professor who teaches elementary {user_info['language']}. Today's topic is {sub_topic} on the {main_topic} chapter, and the learning objective is ```{learning_objective}```. You need to prepare a quiz assessing the students capabilities regarding the given lecture.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_message
                    }
                ]
            }
        ]
    )
    quiz = message.content[0].text
    structured_quiz = []
    for question in re.findall(r"<question>.*?</question>", quiz, re.DOTALL):
        answer_search = re.search(r"<answer>.*?</answer>", question, re.DOTALL)
        if answer_search is None:
            continue
        answer = answer_search.group()[8:-9]
        question = question[:answer_search.span(0)[0]] + question[answer_search.span(0)[1]:]
        translation_search = re.search(r"<translate>.*?</translate>", question, re.DOTALL)
        if translation_search is None:
            continue
        translation = translation_search.group(0)[11:-12]
        question = question[:translation_search.span(0)[0]] + "||->" + answer + "<-||" + question[translation_search.span(0)[1]:]
        question = question[10:-11].replace("<translate>", "||-> ").replace("</translate>", " <-||")
        structured_quiz.append({
            "sentence": question.strip(),
            "answer": translation.strip(),
            "translation": answer.strip()
        })
    return structured_quiz


def prepare_quiz_blank_space(user_info, main_topic, sub_topic, learning_objective, teaching, prev_info=None):
    user_message = ("Prepare me 10 questions as a blank space quiz. Each question should be in between <question> tags. Each question should include a phrase in between <blank> tags and the student will be asked to predict these phrases. Each question should include English complete description in between ()."
                    "For instance, a question structure can be like the following:\n"
                    f"<question>{user_info['language']} sentence related to the lecture and <blank>here is the phrase</blank> that will predicted by the student (here will be the description of the sentence)</question>"
                    f""
                    f"The questions should be related to the material discussed in the lecture. Consider that learning objective is '{learning_objective}'. Prepare beginner level questions and only ask what is taught in the lecture.\n"
                    f"\nThe lecture:")
    if prev_info is not None:
        user_message += f"\n{prev_info}"
    for part in teaching:
        if part['role'] == "user":
            tag = "Student"
        else:
            tag = "Teacher"
        current_line = f"<{tag}>{part['content'][0]['text']}</{tag}>"
        user_message += "\n" + current_line

    user_message += "\n\nGive me the questions."

    message = client.messages.create(
        model=model,
        max_tokens=1000,
        temperature=0,
        system=f"You are a professor who teaches elementary {user_info['language']}. Today's topic is {sub_topic} on the {main_topic} chapter, and the learning objective is ```{learning_objective}```. You need to prepare a quiz assessing the students capabilities regarding the given lecture.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_message
                    }
                ]
            }
        ]
    )
    quiz = message.content[0].text
    structured_quiz = []
    for question in re.findall(r"<question>.*?</question>", quiz, re.DOTALL):
        blank_search = re.search(r"<blank>.*?</blank>", question, re.DOTALL)
        if blank_search is None:
            continue
        structured_quiz.append({
            "sentence": (question[:blank_search.span(0)[0]] + " ____________ " + question[blank_search.span(0)[1]:])[10:-11].strip(),
            "answer": blank_search.group(0)[7:-8].strip()
        })
    return structured_quiz


def answer_question(user_info, sub_topic, main_topic, learning_objective, teaching):
    message = client.messages.create(
        model=model,
        max_tokens=1000,
        temperature=0,
        system=f"You are a professor who teaches elementary {user_info['language']}. Today's topic is {sub_topic} on the {main_topic} chapter, and the learning objective is ```{learning_objective}```. Do not ask any question to the student. Speak in English!",
        messages=teaching
    )

    teacher_text = message.content[0].text
    teacher_text += "\nYou can ask questions related to the topics discussed or would you like me to continue?"
    teaching.append({
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": teacher_text
            }
        ]
    })

    return teaching, teacher_text


def teach_learning_objective(user_info, sub_topic, main_topic, learning_objective, teaching, failed_info=None):
    if teaching is None:
        user_prompt = f"Hello, my name is {user_info['name']}. Give me regarding class helping to acquire the learning objective \"{learning_objective}\" in the {sub_topic} topic. Please help me to understand the lesson with comprehensive . Describe it in English!"

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
        user_prompt = f"Give me regarding class helping to acquire the learning objective \"{learning_objective}\" in the {sub_topic} topic."

        if failed_info is not None:
            user_prompt += '\n' + failed_info

        user_prompt += "\nDescribe it in English!"
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
        system=f"You are a professor who teaches elementary {user_info['language']}. Today's topic is {sub_topic} on the {main_topic} chapter, and the learning objective is ```{learning_objective}```. Do not ask any question to the student. Speak in English!",
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
    user_prompt = f"Define the core learning objectives of the {sub_topic} topic. The learning objective should only be correlated with the {sub_topic} topic but not coincide with others. List each related objective in between <objective> tags. There should be exactly 3 learning objectives. Each objective should be unique. Think like we are splitting the {sub_topic} topic into 3 parts."

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
    for objective in re.findall(r"<objective>.*?</objective>", message.content[0].text, re.DOTALL):
        objectives.append({"objective": objective[11:-12].strip(), "state": "not_known", "lesson": []})

    return objectives


if __name__ == '__main__':

    relevant_check_enabled = False

    os.makedirs('conversations', exist_ok=True)

    API_KEY = os.getenv("API_KEY")
    if API_KEY is None:
        if os.path.exists("api_key.txt"):
            with open("api_key.txt", "r") as f:
                API_KEY = f.read().strip()
    
    if API_KEY is None:
        print("No API key found. Please provide an API key or create an api_key.txt file in the same directory.")
    else:
        # model = "claude-3-haiku-20240307"
        # model = "claude-3-5-haiku-20241022"
        model = "claude-3-5-sonnet-latest"
        intentions = ["proceed", "quit", "go_to_main_topics", "go_to_sub_topics", "exit_quiz", "exit_lesson", "proceed_to_quiz", "question"]
        # TODO genel olarak intention related kisimlar gozden gecirilecek
        # 10. state'ten 2 4 statelerine gecisi inceleyecegim
        client = anthropic.Anthropic(api_key=API_KEY)
        conv_id, conv, sm, ih, ls = organizer_by_state(state=0)
        try:
            with open(f"conversations/{conv_id}.json", "w") as f:
                json.dump({"conversation": conv, "state_machine": sm, "intention_history": ih}, f, indent=4)
        except:
            with open(f'state_machine_{ls}.json', 'r') as f:
                sm = json.load(f)
                conv = sm['conversation']
            with open(f'intention_history_{ls}.json', 'r') as f:
                ih = json.load(f)
            sm['conversation'] = conv
            with open(f"conversations/{conversation_id}.json", "w") as f:
                json.dump({"conversation": conv, "state_machine": sm, "intention_history": ih}, f, indent=4)
