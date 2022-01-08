#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram import (
    Update, 
    ForceReply, 
    ReplyKeyboardMarkup,
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)
from telegram.ext import (Updater, 
    CommandHandler, 
    MessageHandler,
    Filters, 
    CallbackContext,
    PicklePersistence,
    ConversationHandler,
    CallbackQueryHandler
)

CREATING_MEETING, CREATED_MEETING = range(2)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context.
# def start(update: Update, context: CallbackContext) -> None:
#     """Send a message when the command /start is issued."""
#     user = update.effective_user
#     context.chat_data['user_list'] = [] #Initialise user_dict

#     update.message.reply_markdown_v2(
#         fr'Hi {user.mention_markdown_v2()}\!',
#         reply_markup=ForceReply(selective=True),
#     )


# def user_list_to_str(userlist: list) -> str:
#     return '\n'.join([user['first_name'] for user in userlist])


# def join_command(update: Update, context: CallbackContext) -> None:
#     """Add the user to a userlist"""
#     user = update.effective_user
#     username = user['first_name']
           
#     if user not in context.chat_data['user_list']:
#         context.chat_data['user_list'].append(user)

#     update.message.reply_text(f"You have joined the game, {username}! :)\n"
#     f"These are the players currently in the game:{user_list_to_str(context.chat_data['user_list'])}\n"
#     "Bye!"
#     )

#     context.bot.send_message(user['id'],
#     "Hi, a pm from the bot")



# def create_meeting(update: Update, context: CallbackContext) -> int:
#     #Update State
#     context.chat_data['state'] = CREATING_MEETING

#     #Initialise the list of meeting participants and save it to context
#     context.chat_data['meeting_participants'] = set()
    
#     #Construct the inline keyboard
#     keyboard = [
#         [InlineKeyboardButton('Join', callback_data='1')]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
    
#     #Get username of the sender
#     user = update.effective_user
#     username = user['first_name']
    
#     #Send back the reply
#     update.message.reply_text(f'A new meeting has been created by {username}. Click below to join:',
#     reply_markup=reply_markup)
    

# def join_meeting(update: Update, context: CallbackContext) -> None:

#     query = update.callback_query
#     user = update.effective_user
#     print(user, 'has selected to join the meeting.')

#     query.answer()
#     context.chat_data['meeting_participants'].add(user['id'])
#     print('and now the current set of users is', context.chat_data['meeting_participants'])

# def submit_meeting(update: Update, context: CallbackContext) -> None:
#     """Finalise the list of meeting participants."""
#     update.message.reply_text('The meeting will proceed with the following members')
#     context.chat_data['state'] = CREATED_MEETING

def start(update: Update, context: CallbackContext) -> None:
    #Check if the message is sent in a group
    if update.message.chat.type in ['supergroup', 'group']:
        context.chat_data['late_list'] = set()
        print('starting up...')
        update.message.reply_text('Starting...')
    elif update.message.chat.type == 'private':
        param_value = context.args[0]
        
        update.message.reply_text('thing')


def stop(update: Update, context: CallbackContext) -> None:
    #Check if the message is sent in a group
    if update.message.chat.type in ['supergroup', 'group']:
        if 'late_list' in context.chat_data: context.chat_data.pop('late_list')
        print('stopping...')
        update.message.reply_text('Stopping...')


def arrow(update: Update, context: CallbackContext) -> None:
    #Check if the message is sent in a group
    """Arrow a user message."""
    replied_message = update.message.reply_to_message
    print('===========')
    print('there is an update!!!!')
    print(update)

    print('===========')

    if update.message.chat.type in ['supergroup', 'group']:
        if replied_message:
            sender = replied_message.from_user
            if sender:
                context.chat_data['late_list'].add(sender)
                reply_string = 'Uh oh,\n\n' + \
                    '\n'.join([i['first_name'] for i in context.chat_data['late_list']]) + \
                    '\nis late.'
                
                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Start guessing", url='https://t.me/humanrace_bot?start=join')]])

                update.message.reply_text(reply_string, reply_markup=reply_markup)
            

# def voting(update: Update, context: CallbackContext) -> None:
#     '''
    
#     '''
#     penis = 'big'
#     id = 'Li Ren'
#     if penis == 'big' and id == 'Li Ren':
#         print ('UwU Daddy OwO')

#     print('asdf')
#     query = update.callback_query
#     query.answer()

#     context.bot.send_message(update.effective_user['id'], "hi")

'''
To do
1. Get profile picture
2. Voting system
3. Bot to pm user
'''


# def done(update: Update, context: CallbackContext) -> int:
#     """When user is done with conversation (Endpoint)"""
#     update.message.reply_text("End")
#     return ConversationHandler.END

def main() -> None:
    persistence = PicklePersistence(filename='multiuserbot')
    updater = Updater('5022990598:AAEavOAlXva7sMIOOz2eLCIMwDjhQmPaiew', persistence=persistence) # Create the Updater and pass it your bot's token.
    dispatcher = updater.dispatcher # Get the dispatcher to register handlers

    # # on different commands - answer in Telegram
    # dispatcher.add_handler(CommandHandler("start", start))
    # dispatcher.add_handler(CommandHandler("help", help_command))
    # dispatcher.add_handler(CommandHandler("join", join_command))

    # dispatcher.add_handler(CommandHandler('createmeeting', create_meeting))
    # dispatcher.add_handler(CallbackQueryHandler(join_meeting))
    # dispatcher.add_handler(CommandHandler('submitmeeting', submit_meeting))
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('late', arrow))
    dispatcher.add_handler(CommandHandler('yamete', stop))
    # on non command i.e message - echo the message on Telegram
    #dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    updater.start_polling() #Start
    updater.idle() #Stop if Ctrl-C

if __name__ == '__main__':
    main()