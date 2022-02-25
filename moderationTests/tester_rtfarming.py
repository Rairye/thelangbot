# Tester for checking for possible attempts to farm retweets.

import os, importlib, time
from mocks import mock_t
import traceback

mydb = None
mycursor = None

#Sets a threshold for an upper limit of tweets within a certain time period. Users who exceed this threshold are ignored and none of their tweets within that time period are retweeted.
tweetthreshold = 5

#Checks to see if the mysql module is installed and, when it is, the database and cursor are initialized. 
def setupDb() -> None:
    mysql = None
    try:
        mysql = importlib.import_module("mysql.connector")
    except:
        print(traceback.format_exc(), flush=True)
        return
        
    global mydb, mycursor
    
    try:
        mydb = mysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=os.getenv("DB_DB"))
        mycursor = mydb.cursor()
    except:
        print(traceback.format_exc(), flush=True)
        

def getBlacklist() -> set:
    if mycursor == None:
        return set([])

    try:
        mycursor.execute(
            "SELECT * FROM blacklist")
        myresult = mycursor.fetchall()
        usernames = set([row[0] for row in myresult])
        return usernames
    except:
        print(traceback.format_exc(), flush=True)
        return set([])
        
def getSupporters() -> set:
    if mycursor == None:
        return set([])

    try:
        mycursor.execute(
            "SELECT * FROM supporter")
        myresult = mycursor.fetchall()
        usernames = set([row[0] for row in myresult])
        return usernames
    except:
        print(traceback.format_exc(), flush=True)
        return set([])
        
def retrieveLastSeenId() -> int:
    if mycursor == None:
        return 0

    try:
        mycursor.execute("SELECT * FROM tweet")
        myresult = mycursor.fetchall()
        return myresult[0][1]
    except:
        print(traceback.format_exc(), flush=True)
        return 0


def storeLastSeenId(lastSeenId: int) -> None:
    if mycursor == None:
        return

    try:
        exampleId: int = (lastSeenId)
        mycursor.execute("UPDATE tweet SET tweetId = '%s' WHERE id = 1", (exampleId,))
        mydb.commit()
        print(mycursor.rowcount, "record(s) affected", flush=True)

    except:
        print(traceback.format_exc(), flush=True)

    return

def getUserTweetMap(tweets : [], blackList : set([])) -> {}:
    userTweetMap = {}
    
    for tweet in tweets:
        twitterUser: str = tweet.user.screen_name
        if twitterUser in blackList:
            continue
        
        userTweets = userTweetMap.get(twitterUser, [])
        if len(userTweets) == 0:
            userTweetMap[twitterUser] = [tweet]
        else:
            userTweets.append(tweet)

    return userTweetMap

#By default, databases are not updated.
def main(tweets : list, updateDB = False) -> None:
    # Obtain last seen tweet
    lastSeenId: int = retrieveLastSeenId()
    print("Last seen tweet: " + str(lastSeenId) + "\n", flush=True)

    # Setup current last seen tweet to be the previous one
    # This is just in case there are no items in the iterator
    currLastSeenId: int = lastSeenId

    # Get blacklist here
    blackList : set = getBlacklist()
        
    # Get supporters here
    supporters : set = getSupporters()

    userTweetMap = getUserTweetMap(tweets, blackList)

    for twitterUser in  userTweetMap:
        tweets =  userTweetMap[twitterUser]
        tweet_count = len(tweets)

        if tweet_count  > tweetthreshold:
            continue

        for i in range(min(2, tweet_count)):
            tweet = tweets[i]

            try:

                # Like tweet if supporter
                if twitterUser in supporters:
                    tweet.favorite()
                    print("Liking tweet by" + twitterUser, flush=True)

                # Retweet post
                print("Retweet Bot found tweet by @" + 
                    twitterUser + ". " + "Attempting to retweet...", flush=True)
                tweet.retweet()
                print(tweet.text, flush=True)
                print("Tweet retweeted!", flush=True)

                # Update last seen tweet with the newest tweet (bottom of list)
                currLastSeenId = tweet.id
                time.sleep(5)

            except StopIteration:
                print("Stopping...", flush=True)
                break
            
            except Exception:
                print(traceback.format_exc(), "Tweet id: " + str(tweet.id), flush=True)


    # After iteration, store the last seen tweet id (newest)
    # Only store if it is different and updateDB == True
    if(updateDB == True and lastSeenId != currLastSeenId):
        storeLastSeenId(currLastSeenId)
        print("Updating last seen tweet to: " +
        str(currLastSeenId) + "\n", flush=True)

    return


if __name__ == "__main__":
    setupDb()

    #There are 6 tweets from the same user. Since tweetthreshold = 5, none of those tweets will be retweeted. 

    print("\nThere are 6 tweets from the same user. Since tweetthreshold = 5, none of those tweets will be retweeted. ", flush=True)

    mock_t_list = [mock_t("user", "I study English."),
                mock_t("user", "I study Japanese."),
              mock_t("user", "I study Korean."),
              mock_t("user", "I study English."),
                mock_t("user", "I study Japanese."),
                mock_t("user", "I study English."),

              ]

    print("\nTest 1 complete.", flush=True)

    
    main(mock_t_list)

    #There are 5 tweets from the same user. Since tweetthreshold = 5, only the first 2 tweets will be retweeted. 

    print("\nThere are 5 tweets from the same user. Since tweetthreshold = 5, only the first 2 tweets will be retweeted.", flush=True)
    
    mock_t_list = [mock_t("user", "I study English."),
                mock_t("user", "I study Japanese."),
              mock_t("user", "I study Korean."),
              mock_t("user", "I study English."),
                mock_t("user", "I study Japanese."),

              ]
    
    main(mock_t_list)

    print("\nTest 2 complete.", flush=True)

    
    if mycursor != None:
        mycursor.close()
    if mydb != None:
        mydb.close()
        
    print("\nRetweet function completed and db connection closed", flush=True)
