import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import hashlib, binascii, os
import pickle

engine = create_engine("sqlite:///:memory:")#, echo = True)
Session = sessionmaker(bind=engine)

Base = declarative_base()

from sqlalchemy import Column, Integer, String, Table, ForeignKey, Index, and_, exists

user_room_mapping = Table('usersrooms', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('room_id', Integer, ForeignKey('rooms.id'))
)

def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')
 
def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                  provided_password.encode('utf-8'), 
                                  salt.encode('ascii'), 
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


class Role(Base):
	__tablename__ = "roles"
	id = Column(Integer, primary_key = True)
	name = Column(String, unique = True)
	#######################

USER_ROLE = Role(name = 'user')

class User(Base):
	__tablename__ = "users"
	id = Column(Integer, primary_key = True)
	first_name = Column(String)
	last_name = Column(String)
	password = Column(String)
	rooms = relationship("Room", secondary = user_room_mapping, back_populates = "users")
	owning = relationship('Room', back_populates = "owner")
	role_id = Column(Integer, ForeignKey('roles.id'))
	role = relationship('Role')
	Index('unique_users', first_name, last_name, unique=True)

	def __init__(self, *args, **kwargs):
		super(User, self).__init__(*args, **kwargs)
		self.password = hash_password(self.password)
	
	def check_password(self, password):
		return verify_password(self.password, password)

	def __repr__(self):
		return "User {0.first_name} {0.last_name}".format(self)
	
	@staticmethod
	def by_id(session, user_id):
		return session.query(User).filter(User.id == user_id).first()

	@staticmethod
	def create(session, first_name, last_name, password):
		if(session.query(exists().where(and_(User.first_name == first_name, User.last_name == last_name))).scalar()):
			return None
		moi = User(first_name = first_name, last_name = last_name, password = password)
		session.add(moi)
		session.commit()
		return moi

	@staticmethod
	def find(session, first_name, last_name, password):
		user = session.query(User).filter(and_(User.first_name == first_name, User.last_name == last_name)).first()
		if(user == None):
			return None
		else:
			if(user.check_password(password)):
				return user
			else:
				return None


class Room(Base):
	__tablename__ = "rooms"
	id = Column(Integer, primary_key = True)
	name = Column(String)
	users = relationship("User", secondary = user_room_mapping, back_populates = "rooms")
	owner_id = Column(Integer, ForeignKey("users.id"))
	owner = relationship('User', back_populates = "owning")

	def __init__(self, *args, **kwargs):
		super(Room, self).__init__(*args, **kwargs)
		self.users.append(self.owner)
	
	def __repr__(self):
		return "Room " + str(pickle.dumps(self.__dict__))
	
	@staticmethod
	def by_id(session, room_id):
		return session.query(Room).filter(Room.id == room_id).first()
	
	def add_user(self, session, user):
		self.users.append(user)
		session.commit()
	
	def remove_user(self, session, user):
		self.users.remove(user)
		session.commit()

	@staticmethod
	def list_rooms(session, user):
		rooms = []
		results = session.query(Room)
		for room in results:
			val = {'id' : room.id, 'name' : room.name}
			val['inside'] = (room in user.rooms)
			rooms.append(val)	
		return rooms

Base.metadata.create_all(engine)


session = Session()

moi = User(first_name = "Jean-Claude", last_name = "Dupont", password = "sudowoo")
lui = User(first_name = "Patoche", last_name = "Marx", password = "fufufufu")
ma_salle = Room(name = "Ma salle", owner = moi)
sa_salle = Room(name = "Sa salle", owner = lui)
session.add(moi)
session.add(lui)
session.add(ma_salle)
session.add(sa_salle)
session.commit()
session.close()
