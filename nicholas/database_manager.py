from pymongo import MongoClient
from pprint import pprint
from dotenv import dotenv_values
import datetime
from bson.objectid import ObjectId
import pytz
##calculated delta is the correction needed to make. added to actual time to get user time.
##historical data is an array of time reached - time supposed to reach. + indicates that person was late, negative means early.

config = dotenv_values(".env")
client = MongoClient(config["DB_URL"])
meeting_collection = client.data.meetingTable
hist_collection = client.data.histTable
sgt = pytz.timezone('Singapore')

def TestDBConnection():
  # connect to MongoDB, change the << MONGODB URL >> to reflect your own connection string
  client = MongoClient(config["DB_URL"])
  db=client.admin
  # Issue the serverStatus command and print the results
  serverStatusResult=db.command("serverStatus")
  pprint(serverStatusResult)

def create_user(user_id,username):
  db=client.data
  does_user_exist = query_user(user_id)
  if does_user_exist is None:
    user = {
      'userId':str(user_id),
      'username':str(username),
      'historicalData':[],
      'calculatedDelta':0,
      'participatingMeetings':[],
    }
    result = db.histTable.insert_one(user)
    return result
  else:
    #User already exists.
    return False

def query_user(user_id):
  try:
    user = hist_collection.find({'userId':str(user_id)}).next()
  except StopIteration:
    return None
  else:
    return user

def add_meeting_to_user(user_id,meeting_id):
  user = query_user(user_id)
  meeting = query_meeting(meeting_id)
  if user is None:
    raise Exception("User does not exist")
  if meeting is None:
    raise Exception("Meeting does not exist")
  hist_collection.update_one({'userId':str(user_id)},{'$push':{'participatingMeetings':meeting_id}})

def remove_meeting_from_user(user_id,meeting_id):
  user = query_user(user_id)
  meeting = query_meeting(meeting_id)
  if user is None:
    raise Exception("User does not exist")
  if meeting is None:
    raise Exception("Meeting does not exist")
  participating_meetings = user["participatingMeetings"]
  participating_meetings.remove(ObjectId(meeting_id))
  hist_collection.update_one({'userId':str(user_id)},{'$set':{'participatingMeetings':participating_meetings}})


def query_meeting(meeting_id):
  try:
    user = meeting_collection.find({'_id':ObjectId(str(meeting_id))}).next()
  except StopIteration:
    return None
  else:
    return user
    
def create_meeting(date_time,user_id):

  user = query_user(user_id)
  if user is None:
    raise Exception("User does not exist")
  else:
    ## To add: date time type error handling
    if date_time.tzinfo is None or date_time.tzinfo.utcoffset(d) is None:
      actual_time = sgt.localize(date_time)
    else:
      actual_time = date_time
    meeting = {
      "actualTime": actual_time,
      "participants": [{"userId":str(user_id),"userTime":actual_time}],
      "organiser":str(user_id)
    }
    _id = meeting_collection.insert_one(meeting)
    add_meeting_to_user(user_id,_id.inserted_id)
    return str(_id.inserted_id)

def get_meeting_time(meeting_id,user_id):
  user = query_user(user_id)
  meeting = query_meeting(meeting_id)
  if user is None:
    raise Exception("User does not exist")
  if meeting is None:
    raise Exception("Meeting does not exist")
  calculated_delta = user["calculatedDelta"]
  actual_time = pytz.utc.localize(meeting["actualTime"]).astimezone(sgt)
  return actual_time + datetime.timedelta(seconds = calculated_delta)

def update_meeting(meeting_id,user_id):
  user = query_user(user_id)
  meeting = query_meeting(meeting_id)
  if user is None:
    raise Exception("User does not exist")
  if meeting is None:
    raise Exception("Meeting does not exist")
  user_time = get_meeting_time(meeting_id,user_id)
  for participant in meeting["participants"]:
    if participant["userId"] == str(user_id):
      raise Exception("User already part of meeting")
  payload = {
    "userId":str(user_id),
    "userTime": user_time
  }
  add_meeting_to_user(user_id,meeting_id)
  return meeting_collection.update_one({'_id':ObjectId(meeting_id)},{'$push':{'participants': payload}})

def confirm_time(meeting_id,user_id,actual_user_time):

  user = query_user(user_id)
  meeting = query_meeting(meeting_id)
  if user is None:
    raise Exception("User does not exist")
  if meeting is None:
    raise Exception("Meeting does not exist")
  supposed_time_to_meet = None
  for participant in meeting["participants"]:
    if participant["userId"] == str(user_id):
      supposed_time_to_meet = pytz.utc.localize(participant["userTime"]).astimezone(sgt)
  if supposed_time_to_meet is None:
    raise Exception("User not part of meeting")

  if actual_user_time.tzinfo is None or actual_user_time.tzinfo.utcoffset(d) is None:
    actual_user_time = sgt.localize(actual_user_time)  
  time_difference = actual_user_time - supposed_time_to_meet
  time_difference = int(time_difference.total_seconds())
  hist_collection.update_one({'userId':str(user_id)},{'$push':{'historicalData':time_difference}})
  remove_meeting_from_user(user_id,meeting_id)
  update_user_delta(user_id)

def update_user_delta(user_id):
  DECAY_RATIO = 5/6
  user = query_user(user_id)
  historical_data = user['historicalData']
  length = len(historical_data)

  if length > 5:
    multiplier = 1
  else:
    multiplier = length * 0.1 + 0.4

  numerator = 0
  for index,time_difference in enumerate(reversed(historical_data)):
    numerator += time_difference * pow(DECAY_RATIO,index)
  denominator = (1-pow(DECAY_RATIO,length))/(1-DECAY_RATIO)
  
  delta = -int(multiplier * numerator/denominator)
  hist_collection.update_one({'userId':str(user_id)},{'$set':{'calculatedDelta':delta}})
  
def get_user_meetings(user_id):
  user = query_user(user_id)
  if user is None:
    raise Exception("User does not exist")

  meetings = []
  for meeting_id in user["participatingMeetings"]:
    meeting = query_meeting(str(meeting_id))
    organiser_name = query_user(meeting["organiser"])["username"]
    meeting_time = list(filter(lambda user: user["userId"] == str(user_id), meeting['participants']))[0]["userTime"]
    meeting_time = pytz.utc.localize(meeting_time).astimezone(sgt)
    meetings.append({
      "organiser_name":organiser_name, 
      "meeting_time":meeting_time, 
      "meeting_id":meeting_id})
  return meetings

def get_participants(meeting_id):
  meeting = query_meeting(meeting_id)
  if meeting is None:
    raise Exception("Meeting does not exist")

  users = []
  for user_id in meeting["participants"]:
    user = query_user(user_id)
    users.append(user["username"])
  return users