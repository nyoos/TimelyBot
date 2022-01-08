import logging
import datetime

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

from database_manager import (
    create_user,
    create_meeting,
    update_meeting,
    confirm_time,
    get_meeting_time,
    get_user_meetings
)

CHOOSING_TIME, CONFIRMING_JOIN, WAITING_MEETING_CHOICE = range(3)
JOIN_MEETING_PAYLOAD = 'join_meeting_'

BOT_NAME = 'humanrace_bot'
BOT_URL = 'https://t.me/' + BOT_NAME 

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

#SUNI FUNCTIONS

# def create_user(user_id, username):
#     print('SUNI FUNCTION: USER CREATED')
#     pass

# def create_meeting(date_time, user_id):
#     return '420'

# def update_meeting(meeting_id, user_id):
#     print('MEETING UPDATED')
#     pass

# def confirm_time(meeting_id, user_id, actual_user_time):
#     print('TIME CONFIRMED')
#     pass

# def get_meeting_time(meeting_id, user_id):
#     return '69'

# def get_user_meetings(user_id):
#     return [{'organiser_name':'Sun I', 'meeting_time':datetime.datetime(2022, 5, 5, 5, 5, 5), 'meeting_id':'4'},
#         {'organiser_name':'Li Ren', 'meeting_time':datetime.datetime(2022, 6, 6, 6, 6, 6), 'meeting_id':'20'}]


#HELPER FUNCTION

def ensure_personal_chat(update: Update, context: CallbackContext):
    if update.message.chat.type in ['supergroup', 'group']:
        update.message.reply_text(f'You can only use this command in a personal chat with the bot, <a href="{BOT_URL}">here</a>.', parse_mode='HTML')
        return False
    elif update.message.chat.type == 'private':
        return True
    else:
        return False

#START POINT HANDLER

def start(update: Update, context: CallbackContext):
    #Check if the message is sent in a group
    if ensure_personal_chat(update, context):
        user_id = update.effective_user['id']
        user_name = update.effective_user['username']
        if create_user(user_id, user_name):  
            update.message.reply_text('I have added you into my database, ' + str(user_name))


#CREATE MEETING HANDLER

def create_meeting_entry(update: Update, context: CallbackContext):
    start(update, context)
    #Entry point for /createmeeting
    try:
        if ensure_personal_chat(update, context):
            update.message.reply_text('Hi, please choose a date/time in the format YYYY-MM-DD hh:mm:ss (insert the date markup here for user to select a datetime), or type "Cancel" to cancel.')
            return CHOOSING_TIME
    except Exception as e:
        update.message.reply_text('Error: ' + str(e))
        return ConversationHandler.END

        
def create_meeting_time_success(update: Update, context: CallbackContext):
    #Create a new meeting.
    
    try:

        user_id = update.effective_user['id']
        date_time = datetime.datetime.strptime(update.message.text, '%Y-%m-%d %H:%M:%S')

        meeting_id = create_meeting(date_time=date_time, user_id=user_id)
        meeting_link = f'{BOT_URL}?start={JOIN_MEETING_PAYLOAD + meeting_id}'

        update.message.reply_text(f'Saving a new meeting with a certain time, this is your link: \n \
            <a href="{meeting_link}">{meeting_link}</a>', parse_mode='HTML')
        return ConversationHandler.END

    except Exception as e:
        update.message.reply_text('Error: ' + str(e))
        return ConversationHandler.END

def create_meeting_time_tryagain(update: Update, context: CallbackContext):
    update.message.reply_text('Sorry, I do not understand that date. Please try again.')
    return CHOOSING_TIME

def create_meeting_time_cancel(update: Update, context: CallbackContext):
    update.message.reply_text('Ok, cancelling your meeting.')
    return ConversationHandler.END


#JOIN MEETING HANDLER

def join_meeting_entry(update: Update, context: CallbackContext):
    start(update, context)
    meeting_id = context.args[0][13:]
    user_id = update.effective_user['id']
    meeting_time = get_meeting_time(meeting_id=meeting_id, user_id=user_id)
    
    keyboard = [
        [
            InlineKeyboardButton('Confirm', callback_data='Confirm'),
            InlineKeyboardButton('Cancel', callback_data='Cancel')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_string = f'Your meeting time is {meeting_time}\n\n Do you want to confirm?'

    context.user_data['join_meeting'] = {'meeting_id':meeting_id, 'meeting_time':meeting_time}

    update.message.reply_text(reply_string, reply_markup=reply_markup)
    #return CONFIRMING_JOIN

def join_meeting_button(update: Update, context: CallbackContext):
    #Handles the confirmation or cancel button
    query = update.callback_query
    query.answer()

    user_id = update.effective_user['id']
    if 'join_meeting' in context.user_data:
        meeting_id, meeting_time = context.user_data['join_meeting']['meeting_id'], context.user_data['join_meeting']['meeting_time']
        if query.data == 'Confirm':
            try:
                update_meeting(meeting_id=meeting_id, user_id=user_id)
                query.message.reply_text('You have chosen to join this meeting. Please remember to stick to your meeting time!')
            except Exception as e:
                query.message.reply_text('Error: ' + str(e))
        else:
            query.message.reply_text('Ok, cancelling your meeting.')
    
    else:
        query.message.reply_text('There was an error joining the meeting, please try again.')

    return ConversationHandler.END


#CHECKIN HANDLER

def checkin_meeting_entry(update: Update, context: CallbackContext):
    if ensure_personal_chat(update, context):
        start(update, context)
        user_id = update.effective_user['id']
        meetings = get_user_meetings(user_id)
        
        meeting_list_string = '\n'.join([f'{idx + 1}. {meeting["organiser_name"]}\'s meeting at {meeting["meeting_time"].strftime("%m/%d/%Y, %H:%M:%S")}' \
            for idx, meeting in enumerate(meetings)])
        
        context.user_data['checkin_meeting_validation'] = range(1, len(meetings) + 1)
        context.user_data['checkin_meeting_meetings'] = meetings

        reply_string = 'Enter the number of the meeting you want to join or type "Cancel" to cancel:\n\n' + meeting_list_string

        update.message.reply_text(reply_string)

        return WAITING_MEETING_CHOICE

def checkin_meeting_confirm(update: Update, context: CallbackContext):
    try:
        value = int(update.message.text)
        if value in context.user_data['checkin_meeting_validation']:
            organiser = context.user_data['checkin_meeting_meetings'][value - 1]['organiser_name']
            #checkin (meeting_id, user_id)
            update.message.reply_text(f'Thanks for conforming your attendance for {organiser}\'s meeting.')
            return ConversationHandler.END
        else:
            raise ValueError        
    except:
        checkin_meeting_tryagain(update, context)

def checkin_meeting_tryagain(update: Update, context: CallbackContext):
    update.message.reply_text('Invalid input, please try again.')
    return WAITING_MEETING_CHOICE

def checkin_meeting_cancel(update: Update, context: CallbackContext):
    update.message.reply_text('Cancelling the checkin.')
    return ConversationHandler.END


#HELP text

def help(update: Update, context: CallbackContext) -> None:
    reply_string = 'You can send the following commands to the bot:\n\n' + \
    '/help: Displays this text\n'  + \
    '/checkin: Checks you into a meeting\n'  + \
    '/createmeeting: Creates a new meeting\n' + \
    '/start: Starts the bot\n'
    update.message.reply_text(reply_string)

def main() -> None:
    persistence = PicklePersistence(filename='multiuserbot')
    updater = Updater('5022990598:AAEavOAlXva7sMIOOz2eLCIMwDjhQmPaiew', persistence=persistence) # Create the Updater and pass it your bot's token.
    dispatcher = updater.dispatcher # Get the dispatcher to register handlers

    #Add START Handler
    dispatcher.add_handler(CommandHandler('start', start, Filters.text & ~Filters.regex(JOIN_MEETING_PAYLOAD)))

    #Add Create Meeting Handler
    create_meeting_handler = ConversationHandler(
        entry_points=[CommandHandler('createmeeting', create_meeting_entry)],
        states={
            CHOOSING_TIME: [
                MessageHandler(Filters.regex(r'^[\d]{4}\-[\d]{2}\-[\d]{2} [\d]{2}:[\d]{2}:[\d]{2}$') & ~Filters.command, create_meeting_time_success),
                MessageHandler(Filters.regex('^Cancel$') & ~Filters.command, create_meeting_time_cancel),
                MessageHandler(Filters.text & ~Filters.command, create_meeting_time_tryagain)                
            ]
        },
        fallbacks=[MessageHandler(Filters.text & ~Filters.command, create_meeting_time_cancel)],
        name='create_meeting_conversation'
    )
    dispatcher.add_handler(create_meeting_handler)

    #Add Join Meeting Handler
    dispatcher.add_handler(CommandHandler('start', join_meeting_entry, Filters.regex(JOIN_MEETING_PAYLOAD)))
    dispatcher.add_handler(CallbackQueryHandler(join_meeting_button))

    #Add Checkin Handler
    checkin_meeting_handler = ConversationHandler(
        entry_points=[CommandHandler('checkin', checkin_meeting_entry)],
        states={
            WAITING_MEETING_CHOICE: [
                MessageHandler(Filters.regex(r'^[\d]+$') & ~Filters.command, checkin_meeting_confirm),
                MessageHandler(Filters.regex(r'^Cancel$') & ~Filters.command, checkin_meeting_cancel),
                MessageHandler(Filters.text & ~(Filters.command|Filters.regex(r'^([\d]+|Cancel)$')), checkin_meeting_tryagain),
            ]
        },
        fallbacks=[MessageHandler(Filters.text & ~Filters.command, checkin_meeting_tryagain)],
        name='create_meeting_conversation'
    )
    dispatcher.add_handler(checkin_meeting_handler)

    dispatcher.add_handler(CommandHandler('help', help))

    updater.start_polling() #Start
    updater.idle() #Stop if Ctrl-C

if __name__ == '__main__':
    main()