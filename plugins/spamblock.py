"""This plugin allows for a fine-grained control over how much the bot says.

This is useful to prevent spamming in crowded rooms and loops with other bots.
To make full use of its protection, load this plugin as the last plugin in
the list.

"""
import time

# The command used to address this plugin.
PREFIX = "!spam "
# Default maximum number of outgoing messages per second per UID.
DEFAULT = 60
# This dictionary holds the rate limiting (messages per UID per minute).  The
# data is stored like this: {uid: [n, m, (year, month, day, hour, minute)]}.
# n Stands for the number of messages in this minute, m for the limit. A limit
# of 0 means that no limiting is applied.
ratelimiting = {}

def process(identity, message, reply):

	# Current time to the minute exact.
	now = time.gmtime()[:5]
	uid = identity.getUid()

	if message.startswith(PREFIX):
		cmd = message[len(PREFIX):]
		if cmd.startswith("rate "):
			try:
				limit = int(cmd[5:])
			except ValueError:
				return (message, reply)
			# If the script reaches this point, the sender sent a correct command.
			try:
				ratelimiting[uid][1] = limit
			except KeyError:
				ratelimiting[uid] = [1, limit, now]
			return (message, limit == 0 and "limit removed" or "k.")

	# Check the number of messages since this minute began:
	try:
		if ratelimiting[uid][2] == now:
			ratelimiting[uid][0] += 1
			limit = ratelimiting[uid][1]
			if 0 < limit < ratelimiting[uid][0]:
				# Stay quiet (reply = None).
				return (message, None)
		else:
			ratelimiting[uid][0] = 1
			ratelimiting[uid][2] = now
	except KeyError:
		ratelimiting[uid] = [1, DEFAULT, now]
	
	return (message, reply)
