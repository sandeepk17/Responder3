import logging
import traceback
from responder3.servers.BASE import ResponderServer, ResponderProtocolTCP
from responder3.packets import POPOKPacket

class POP3(ResponderServer):
	def __init__(self):
		ResponderServer.__init__(self)
		self.protocol = POP3Protocol
		self.curstate = 0
		self.User = None
		self.Pass = None


	def modulename(self):
		return 'POP3'

	def handle(self, data, transport):
		try:
			self.log(logging.DEBUG,'Handle called with data: ' + str(data))

			if self.curstate == 0:
				#send welcome msg
				transport.write(POPOKPacket().getdata())
				self.curstate = 1
				return
			
			elif self.curstate == 1:
				#check if user is sent
				if data[0:4] == "USER":
					self.User = data[5:].strip()
					transport.write(POPOKPacket().getdata())

				elif data[0:4] == "PASS":
					self.Pass = data[5:].strip()

					self.logResult({
						'module': self.modulename(), 
						'type': 'Cleartext', 
						'client': self.peername, 
						'user': self.User, 
						'cleartext': self.Pass, 
						'fullhash': self.User + ':' + self.Pass
					})

					transport.write(POPOKPacket().getdata())

				else:
					self.cmderr()
			else:
				self.cmderr()


		except Exception as e:
			self.log(logging.INFO,'Exception! %s' % (str(e),))
			pass

	def cmderr(self, transport):
		transport.close()


class POP3Protocol(ResponderProtocolTCP):
	
	def __init__(self, server):
		ResponderProtocolTCP.__init__(self, server)
		self._buffer_maxsize = 1*1024

	def _connection_made(self, transport):
		self._server.curstate = 0
		self._server.handle(None, transport)

	def _data_received(self, raw_data):
		return

	def _connection_lost(self, exc):
		return

	def _parsebuff(self):
		#POP3 commands are terminated by new line chars
		#here we grabbing one command from the buffer, and parsing it
		marker = self._buffer.find(b'\r\n')
		if marker == -1:
			return
	
		cmd = self._buffer[:marker].decode('ascii')

		#after parsing it we send it for processing to the handle
		self._server.handle(cmd, self._transport)

		#IMPORTANT STEP!!!! ALWAYS CLEAR THE BUFFER FROM DATA THAT IS DEALT WITH!
		self._buffer = self._buffer[marker + 2 :]

class POP3S(POP3):
	def modulename(self):
		return 'POP3S'