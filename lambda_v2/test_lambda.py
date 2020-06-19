#Imports
#import os
import random
import logging
import json
import prompts
import my_functions as mf

import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Responsejam
        speak_output = "Bienvenido, cómo puedo ayudarte?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# Built-in Intent Handlers
class GetNewFactHandler(AbstractRequestHandler):
    """Handler for Skill Launch and GetNewFact Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GetNewFactIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In GetNewFactHandler")

        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]

        #random_fact = random.choice(data[prompts.FACTS])
        facts = data[prompts.FACTS]
        categories = [c for c in facts.keys()]

        random_topic = random.choice(categories)
        random_fact = random.choice(data[prompts.FACTS][random_topic])

        speech = data[prompts.GET_FACT_MESSAGE].format(random_topic,random_fact)

        handler_input.response_builder.speak(speech).set_card(
            SimpleCard(data[prompts.SKILL_NAME], random_fact))
        return handler_input.response_builder.response

class GetCategoryFactHandler(AbstractRequestHandler):
    """Handler for Skill Launch and GetNewFact Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GetCategoryFactIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In GetCategoryFactHandler")

        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]

        facts = data[prompts.FACTS]
        categories = [c for c in facts.keys()]

        fact_category = mf.get_resolved_value(
        handler_input.request_envelope.request, 'factCategory')
        #fact_category = 'casa'

        logger.info("FACT CATEGORY = {}".format(fact_category))

        if fact_category in categories:
            random_fact = random.choice(data[prompts.FACTS][fact_category])
            speech = data[prompts.GET_FACT_MESSAGE].format(fact_category,random_fact)

            handler_input.response_builder.speak(speech).set_card(
            SimpleCard(data[prompts.SKILL_NAME], random_fact))
            return handler_input.response_builder.response

        else:
            random_topic = random.choice(categories)
            random_fact = random.choice(data[prompts.FACTS][random_topic])
            speech = data[prompts.GET_FACT_MESSAGE].format(random_topic, random_fact)

            handler_input.response_builder.speak(speech).set_card(
            SimpleCard(data[prompts.SKILL_NAME], random_fact))
            return handler_input.response_builder.response


class HelloIntentHandler(AbstractRequestHandler):
    """Handler for Hello Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("HelloIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Buenos dias, bienvenido a la Casa Verde!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )

class YesHandler(AbstractRequestHandler):
    """If the user says Yes, they want another fact."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("YesIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In YesHandler")
        return GetNewFactHandler().handle(handler_input)

class NoHandler(AbstractRequestHandler):
    """If the user says No, then the skill should be exited."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("NoIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In NoHandler")

        return handler_input.response_builder.speak(
            mf.get_random_goodbye()).set_should_end_session(True).response

class GetCategoryFactHandlerOther(AbstractRequestHandler):
    """
    Handler for providing category specific facts to the user.
    The handler provides a random fact specific to the category provided
    by the user. If there is no such category,
    then a custom message to choose valid categories is provided, rather
    than throwing an error.
    """

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("GetCategoryFactIntent_")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In GetCategoryFactHandler")

        fact_category = get_resolved_value(
            handler_input.request_envelope.request, 'factCategory')
        logger.info("FACT CATEGORY = {}".format(fact_category))

        category_facts = [l for l in all_facts if l.get("type") == fact_category]

        if not category_facts:
            slot_value = get_spoken_value(
                handler_input.request_envelope.request, "factCategory")
            if slot_value is not None:
                speak_prefix = "I heard you said {}.".format(slot_value)
            else:
                speak_prefix = ""
            speech = (
                "{} I don't have facts for that category.  You can ask for "
                "A, B or C.  Which one would you "
                "like?".format(speak_prefix))
            reprompt = (
                "Which fact category would you like?")
            return handler_input.response_builder.speak(speech).ask(
                reprompt).response
        else:
            in_skill_response = in_skill_product_response(handler_input)
            if in_skill_response:
                subscription = [
                    l for l in in_skill_response.in_skill_products
                    if l.reference_name == "all_access"]
                category_product = [
                    l for l in in_skill_response.in_skill_products
                    if l.reference_name == "{}_pack".format(fact_category)]

                if is_entitled(subscription) or is_entitled(category_product):
                    speech = "Here's your {} fact: {} {}".format(
                        fact_category, get_random_from_list(category_facts),
                        get_random_yes_no_question())
                    reprompt = get_random_yes_no_question()
                    return handler_input.response_builder.speak(speech).ask(
                        reprompt).response
                else:
                    upsell_msg = (
                        "You don't currently own the {} pack. {} "
                        "Want to learn more?").format(
                        fact_category, category_product[0].summary)
                    return handler_input.response_builder.add_directive(
                        SendRequestDirective(
                            name="Upsell",
                            payload={
                                "InSkillProduct": {
                                    "productId": category_product[0].product_id,
                                },
                                "upsellMessage": upsell_msg,
                            },
                            token="correlationToken")
                    ).response



class HelpIntentHandler(AbstractRequestHandler):
    #Handler for Help Intent.
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "HELP? I NEED SOMEBODY, HEELP!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class LocalizationInterceptor(AbstractRequestInterceptor):
    """
    Add function to request attributes, that can load locale specific data.
    """

    def process(self, handler_input):
        locale = handler_input.request_envelope.request.locale
        logger.info("Locale is {}".format(locale[:2]))

        # localized strings stored in language_strings.json
        with open("language_strings.json") as language_prompts:
            language_data = json.load(language_prompts)
        # set default translation data to broader translation
        data = language_data[locale[:2]]
        # if a more specialized translation exists, then select it instead
        # example: "fr-CA" will pick "fr" translations first, but if "fr-CA" translation exists,
        #          then pick that instead
        if locale in language_data:
            data.update(language_data[locale])
        handler_input.attributes_manager.request_attributes["_"] = data

# Request and Response loggers
class RequestLogger(AbstractRequestInterceptor):
    """Log the alexa requests."""

    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.debug("Alexa Request: {}".format(
            handler_input.request_envelope.request))


class ResponseLogger(AbstractResponseInterceptor):
    """Log the alexa responses."""

    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.debug("Alexa Response: {}".format(response))

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.
sb = SkillBuilder()

#Register intent handlers
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GetNewFactHandler())
sb.add_request_handler(GetCategoryFactHandler())
sb.add_request_handler(YesHandler())
sb.add_request_handler(NoHandler())
#sb.add_request_handler(SampleIntentHandler())
sb.add_request_handler(HelloIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

#Register xception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# Register request and response interceptors
sb.add_global_request_interceptor(LocalizationInterceptor())
sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())

lambda_handler = sb.lambda_handler()
