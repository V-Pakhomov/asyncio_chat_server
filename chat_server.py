import asyncio
from colors import *

class Server(asyncio.Protocol):

	free_users = []
	private_chats = {}
	transports = {}
	names = {}

	def create_private_chat(self, peername):
		if not len(self.free_users):
			self.free_users.append(peername)
			self.transport.write(b"Waiting for chat...\n")
		else:
			teammate = self.free_users.pop(0)
			self.private_chats[peername] = teammate
			self.private_chats[teammate] = peername
			self.transports[peername].write(
				f"{GREEN}You are now chatting with {self.names[teammate]}!{RESET}\n".encode()
			)
			self.transports[teammate].write(
				f"{GREEN}You are now chatting with {self.names[peername]}!{RESET}\n".encode()
			)

	def set_name(self, peername, name):
		name = name[:-2]
		self.names[peername] = name

	def connection_made(self, transport):
		self.transport = transport
		peername = transport.get_extra_info('peername')
		self.transports[peername] = transport
		print(f'Connection from {peername}')
		transport.write(f"{BLUE}Enter your name please{RESET}\n".encode())

	def connection_lost(self, exc):
		peername = self.transport.get_extra_info('peername')
		print(f'Connection lost with {peername}')
		del self.transports[peername]
		if peername in self.free_users:
			self.free_users.remove(peername)
			del self.names[peername]
			return None
		teammate = self.private_chats[peername]
		self.transports[teammate].write(
			f"{RED}Sorry, but {self.names[peername]} has disconnected :({RESET}\n".encode()
		)
		del self.names[peername]
		del self.private_chats[peername]
		del self.private_chats[teammate]
		self.create_private_chat(teammate)

	def data_received(self, data):
		peername = self.transport.get_extra_info('peername')
		try:
			message = data.decode()
		except UnicodeDecodeError:
			return None
		print(f'Recieved data from {peername}: {message}')
		if not peername in self.names:
			self.set_name(peername, message)
			self.create_private_chat(peername)
			return None
		if not peername in self.private_chats:
			self.transport.write(f"{RED}You aren't chatting yet :({RESET}\n")
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
