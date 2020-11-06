import asyncio

class Server(asyncio.Protocol):

	free_users = []
	private_chats = {}
	transports = {}
	names = {}

	def set_name(self, peername, name):
		name = name[:-2]
		self.names[peername] = name

	def connection_made(self, transport):
		self.transport = transport
		peername = transport.get_extra_info('peername')
		self.transports[peername] = transport
		print(f'Connection from {peername}')
		transport.write(b"Enter your name please\n")

	def connection_lost(self, exc):
		peername = self.transport.get_extra_info('peername')
		del self.transports[peername]
		if peername in self.free_users:
			self.free_users.remove(peername)
			del self.names[peername]
			return None
		teammate = self.private_chats[peername]
		self.transports[teammate].write(
			f"Sorry, but {self.names[peername]} has disconnected :(\n".encode()
		)
		del self.names[peername]
		del self.private_chats[peername]
		del self.private_chats[teammate]
		self.free_users.append(teammate)

	def data_received(self, data):
		peername = self.transport.get_extra_info('peername')
		try:
			message = data.decode()
		except UnicodeDecodeError:
			return None
		print(f'Recieved data from {peername}: {message}')
		if not peername in self.names:
			self.set_name(peername, message)
			if not len(self.free_users):
				self.free_users.append(peername)
				self.transport.write(b"Waiting for chat...\n")
			else:
				teammate = self.free_users.pop(0)
				self.transport.write(
					f"You are now chatting with {self.names[teammate]}!\n".encode()
				)
				self.transports[teammate].write(
					f"You are now chatting with {self.names[peername]}!\n".encode()
				)
				self.private_chats[peername] = teammate
				self.private_chats[teammate] = peername
			return None
		if not peername in self.private_chats:
			self.transport.write(b"You aren't chatting yet :(\n")
		else:
			teammate = self.private_chats[peername]
			self.transports[teammate].write(data)


def run_server(host='127.0.0.1', port=10001):
	loop = asyncio.get_event_loop()
	coro = loop.create_server(Server, host, port)
	server = loop.run_until_complete(coro)
	try:
		loop.run_forever()
	except KeyboardInterrupt:
		pass
	server.close()
	loop.run_until_complete(server.wait_closed())
	loop.close()

if __name__ == '__main__':
	run_server()
