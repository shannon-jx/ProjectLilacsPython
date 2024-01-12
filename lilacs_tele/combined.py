import asyncio
import calendar
import requests
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CallbackContext
from datetime import datetime
from typing import Final
# from profanity_check import predict
# import joblib
import re

TOKEN: Final = '6875784681:AAE3F-mYgo414dCSl5zHNRbTuWRs-yiNL_w'
BOT_USERNAME: Final = '@@projectlilacscombinedbot'
PERSPECTIVE_API_KEY: Final = 'AIzaSyCxovLh6TOVpuMs4msnjumyA3BAXc9Ks7E'

### GENERAL COMMANDS

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "<b>Scheduling a time</b>\n"
        "/indicatetime: Indicate your own availability for specific times.\n"
        "/showtimeavailabilities: View the availability of all users for specific times.\n"
        "/showfreetimes: Find common free time slots when everyone is available.\n\n"
        "<b>Scheduling a date</b>\n"
        "/indicatedate: Indicate your own availability for specific dates.\n"
        "/showdateavailabilities: View the availability of all users for specific dates.\n"
        "/showfreedates: Find common free dates when everyone is available."
    )
    await update.message.reply_text(help_text, parse_mode="HTML")

### LANGUAGE FLAGGER
    
# Hard Code a list of vulgar words or patterns
# VULGAR_WORDS = ['grass', 'hate']

# # Helper function to check toxicity using the Perspective API
# def get_toxicity_score(text: str) -> float:
#     endpoint = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
#     url = f"{endpoint}?key={PERSPECTIVE_API_KEY}"

#     document = {"comment": {"text": text}, "languages": ["en"], "requestedAttributes": {"TOXICITY": {}}}
    
#     response = requests.post(url, json=document)
#     result = response.json()

#     return result["attributeScores"]["TOXICITY"]["summaryScore"]["value"]

# # Bot's response to message (ML, then imported list, then hardcode)
# def handle_response(text: str) -> str:
#     text = text.lower()
#     # first, toxicity score using ML
#     toxicity_score = get_toxicity_score(text)
#     if toxicity_score > 0.5: # Edit toxicity threshold here
#         return "Please refrain from using inappropriate language."
#     # second, imported list
#     is_profane = predict([text])[0]
#     if is_profane == 1:
#         return "Please refrain from inappropriate language"
#     # third, hardcode
#     else:
#         for i in VULGAR_WORDS:
#             if i in text:
#                 return "Please refrain from inappropriate language"
#     return "None"
        
# async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     message_type: str = update.message.chat.type
#     text: str = update.message.text

#     print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

#     response: str  # Declare the response variable with a default value
#     if message_type == 'group':
#         if BOT_USERNAME in text:
#             new_text: str = text.replace(BOT_USERNAME, '').strip()
#             response = handle_response(new_text)
#         else:
#             response = handle_response(text)
#     else:
#         response = handle_response(text)

#     print('Bot:', response)

#     # Send the response back to the chat
#     if response != "None":
#         await update.message.reply_text(response)


### SCHEDULING A TIME
        
# Dictionary to store user availabilities and clicked buttons for each group chat
group_data_time = {}

# Command /indicatetime to indicate own availabilities
async def indicate_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    
    # Initialize user data if not exists
    if chat_id not in group_data_time:
        group_data_time[chat_id] = {}
    group_data_time[chat_id][user_id] = {'time_availabilities': set(), 'clicked_buttons': set()}
    
    # Create an inline keyboard
    keyboard = [
        [InlineKeyboardButton("11:00 - 13:00", callback_data="11:00 - 13:00")],
        [InlineKeyboardButton("12:00 - 14:00", callback_data="12:00 - 14:00")],
        [InlineKeyboardButton("13:00 - 15:00", callback_data="13:00 - 15:00")],
        [InlineKeyboardButton("14:00 - 16:00", callback_data="14:00 - 16:00")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await update.message.reply_text("Welcome! Let's start scheduling. Please select your availabilities:", reply_markup=reply_markup)
    # Save the message ID to delete the inline keyboard later
    context.user_data['message_id'] = message.message_id

# Callback function for handling button clicks for command /indicatetime
async def display_button_time(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = update.effective_chat.id  # Get the current chat ID
    button_data = query.data
    # Define the pattern for time button clicks
    time_button_pattern = r'^(11:00 - 13:00|12:00 - 14:00|13:00 - 15:00|14:00 - 16:00)$'
    # Check if the button data matches the pattern
    if re.match(time_button_pattern, button_data):
        # Update user data and clicked buttons
        group_data_time[chat_id][user_id]['time_availabilities'].add(button_data)
        group_data_time[chat_id][user_id]['clicked_buttons'].add(button_data)
        await query.edit_message_text(f"Thank you! Your current availabilities:\n\n <b>{', '.join(group_data_time[chat_id][user_id]['time_availabilities'])}</b> \n\nPlease confirm that this is correct or enter the command again.", parse_mode='HTML')
    else:
        # Trigger the callback for calendar button click
        await display_button_date(update, context)

# Command /showtimeavailabilities to show everyone's availabilities in the current group chat
async def show_time_availabilities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    time_availabilities_message = []
    if chat_id in group_data_time:
        for user_id, user_data in group_data_time[chat_id].items():
            try:
                username = (await context.bot.get_chat_member(chat_id, user_id)).user.username
                time_availabilities_message.append(f"{username}: {', '.join(user_data['time_availabilities'])}")
            except Exception as e:
                print(f"Error fetching username for user_id {user_id}: {e}")
        await update.message.reply_text("Everyone's availabilities:\n" + "\n".join(time_availabilities_message))
    else:
        await update.message.reply_text("No availabilities have been indicated in this group chat yet.")

# Command /showfreetimes to find common free time slots when everyone is available in the current group chat
async def show_free_times(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    # Check if the group has data
    if chat_id in group_data_time:
        # Gather all availabilities
        all_time_availabilities = [user_data['time_availabilities'] for user_data in group_data_time[chat_id].values()]
        # Find common availabilities
        common_time_availabilities = set(all_time_availabilities[0]).intersection(*all_time_availabilities[1:])
        if common_time_availabilities:
            await update.message.reply_text(f"The meeting can be scheduled at the following times: {', '.join(common_time_availabilities)}")
        else:
            await update.message.reply_text("Sorry, no common availabilities found. Please try different times or check your input.")
    else:
        await update.message.reply_text("No availabilities have been indicated in this group chat yet.")


### SCHEDULING A DATE
        
# Dictionary to store user availabilities and last interaction time for each group
group_data = {}

# Command /indicatedate to indicate your own availability for specific dates with an interactive calendar
async def indicate_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    # Use group chat ID as part of the key
    if chat_id not in group_data:
        group_data[chat_id] = {}
    group_data[chat_id][user_id] = {'date_availabilities': set(), 'last_interaction_time': time.time()}
    # Initialize context.user_data if not present
    if 'calendar_year' not in context.user_data:
        today = datetime.today()
        context.user_data['calendar_year'] = today.year
        context.user_data['calendar_month'] = today.month
    # Display an interactive calendar with a "Confirm" button
    await display_calendar_date(update, context, include_confirm_button=True)

# Helper function to display an interactive calendar for command /indicatedate
async def display_calendar_date(update: Update, context: ContextTypes.DEFAULT_TYPE, include_confirm_button=False):
    user_id = update.message.from_user.id  # Get the user ID of the user who initiated the command
    chat_id = update.message.chat_id
    keyboard = []
    header = [InlineKeyboardButton(calendar.month_name[context.user_data['calendar_month']], callback_data='ignore')]
    keyboard.append(header)
    # Days of the week
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    header_row = [InlineKeyboardButton(day, callback_data='ignore') for day in days]
    keyboard.append(header_row)
    # Build the calendar
    month_calendar = calendar.monthcalendar(context.user_data['calendar_year'], context.user_data['calendar_month'])
    for week in month_calendar:
        row = [InlineKeyboardButton(str(day) if day != 0 else " ", callback_data=f'day_{day}') for day in week]
        keyboard.append(row)
    # Add a "Confirm" button
    if include_confirm_button:
        confirm_button = [InlineKeyboardButton("Confirm", callback_data='confirm')]
        keyboard.append(confirm_button)

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Check if the user interacting with the calendar is the same as the user who initiated the command
    if user_id == update.message.from_user.id:
        await update.message.reply_text("Please select your availability using the calendar:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("You are not authorized to interact with this calendar.")

# Callback function for handling calendar button clicks for command /indicatedate
async def display_button_date(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    # Use group chat ID as part of the key
    if chat_id not in group_data:
        group_data[chat_id] = {}

    # Define the pattern for calendar button clicks
    calendar_button_pattern = r'^day_\d+$'

    # Process the selected day only if it matches the pattern
    if re.match(calendar_button_pattern, query.data):
        day = int(query.data.split('_')[1])
        group_data[chat_id][user_id]['date_availabilities'].add(day)
        group_data[chat_id][user_id]['last_interaction_time'] = time.time()

    # Process the "Confirm" button
    elif query.data == 'confirm':
        await query.edit_message_text(f"Thank you! Your current availabilities:\n\n <b>{', '.join(map(str, group_data[chat_id][user_id]['date_availabilities']))}</b> \n\nPlease confirm that this is correct or enter the command again.", parse_mode='HTML')
        return


# Command /showdateavailabilities to show everyone's availabilities
group_data = {}
async def show_date_availabilities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    # Ensure the group data dictionary has the key for the current chat
    if chat_id in group_data:
        date_availabilities_message = "Individual Availabilities:\n"

        for user_id, user_info in group_data[chat_id].items():
            # Use await when calling get_chat_member
            chat_member = await context.bot.get_chat_member(chat_id, user_id)

            # Check if chat_member is not None before accessing attributes
            if chat_member:
                username = chat_member.user.username
                date_availabilities = user_info.get('date_availabilities', set())

                # Append individual availabilities to the message
                date_availabilities_message += f"{username}'s availabilities: {', '.join(map(str, date_availabilities))}\n"

            else:
                date_availabilities_message += "User information not available.\n"

        # Send the message with individual availabilities
        await update.message.reply_text(date_availabilities_message)

    else:
        await update.message.reply_text("Group data not available for this chat.")

# Command /showfreedates to find common free dates when everyone is available.
async def show_free_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    # Ensure the group_data dictionary has the key for the current chat
    if chat_id in group_data:
        all_date_availabilities = [user_info['date_availabilities'] for user_info in group_data[chat_id].values()]
        # Find common free days
        common_free_days = set(range(1, 32)).intersection(*all_date_availabilities)
        await update.message.reply_text(f"Common free days for all users: {', '.join(map(str, common_free_days))}")
    else:
        await update.message.reply_text("Group data not available for this chat.")


### ERROR HANDLING
        
async def context_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused context error {context.error}')

### START BOT

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('help', help_command))

    app.add_handler(CommandHandler('indicatetime', indicate_time))
    app.add_handler(CommandHandler('showtimeavailabilities', show_time_availabilities))
    app.add_handler(CommandHandler('showfreetimes', show_free_times))

    app.add_handler(CommandHandler('indicatedate', indicate_date))
    app.add_handler(CommandHandler('showdateavailabilities', show_date_availabilities))
    app.add_handler(CommandHandler('showfreedates', show_free_dates))

    # Messages
    # app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Buttons
    app.add_handler(CallbackQueryHandler(display_button_time))
    app.add_handler(CallbackQueryHandler(display_button_date))

    # Errors
    app.add_error_handler(context_error)

    # Polls the bot
    print("Polling...")
    app.run_polling(poll_interval=3)
