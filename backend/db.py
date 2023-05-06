import hashlib
from datetime import datetime
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from backend.config import avatar

client = MongoClient('localhost', 27017, username='mongoadmin', password='mongoadmin')
archive = client['archive']
users = archive['users']
pages = archive['pages']
access = archive['access']


# Users
class Role(Enum):
    ADMIN = 1
    EDITOR = 2
    READER = 3
    BOT = 4


class Status(Enum):
    Recent = 1
    Long = 2
    TooLong = 3
    Baned = 4


class Privilage(Enum):
    Read = 'Read'
    Write = 'Write'


def insertUser(user_name: str, email: str, password: str):
    oldId = users.find_one(sort=[("user_id", -1)])
    id = 1
    if oldId is not None and 'user_id' in oldId:
        id = oldId['user_id'] + 1

    avatar_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
    hashed_password = generate_password_hash(password)

    users.insert_one({
        'user_id': id,
        'user_name': user_name,
        'email': email,
        'password': hashed_password,
        'account_status': Status.Recent.value,
        'account_type': Role.BOT.value,
        'is_active': True,
        'signup_time': datetime.now().timestamp(),
        'last_visit': datetime.now().timestamp(),
        'avatar': avatar.gravatar(avatar_hash),
    })


def deleteUser(user_name: str):
    find = users.find_one({"user_name": user_name})
    if find is not None:
        users.delete_one({"user_name": user_name})


def getUser(user_name: str):
    return users.find_one({'user_name': user_name})


def setRole(user_name: str, role: int):
    users.find_one_and_update({'user_name': user_name},
                              {'$set': {"account_type": role}})


def updateLastVisit(user_name: str):
    users.find_one_and_update({'user_name': user_name},
                              {'$set': {"last_visit": datetime.now().timestamp()}})


def getAllUsers():
    return users.find()


# End of User


# Pages
def getPages():
    return pages.find()


def findPage(tag: str):
    return pages.find_one({'tag': tag})


def getFile(tag: str, filename: str):
    find = pages.find_one({"tag": tag})
    return next(filter(lambda x: x['filename'] == filename, find['files']))


def insertPage(owner_id: int, tag: str, title="",
               description="", keywords="", body="", files=[]):
    oldId = pages.find_one(sort=[("page_id", -1)])
    id = 1
    if oldId is not None and 'page_id' in oldId:
        id = oldId['page_id'] + 1

    # Insert the new page into the MongoDB 'pages' collection
    pages.insert_one({
        'page_id': id,
        'title': title,
        'owner_id': owner_id,
        'tag': tag,
        'description': description,
        'keywords': keywords,
        'body': body,
        'files': [{'filename': file.filename, 'content': file.read()} for file in files]
    })

    oldIdA = access.find_one(sort=[("acl_id", -1)])
    idA = 1
    if oldIdA is not None and 'acl_id' in oldIdA:
        idA = oldIdA['acl_id'] + 1

    access.insert_one({
        'acl_id': idA,
        'page_id': id,
        'privilege': Privilage.Read.value,
        'list': [owner_id]
    })
    access.insert_one({
        'acl_id': idA + 1,
        'page_id': id,
        'privilege': Privilage.Write.value,
        'list': [owner_id]
    })


def deletePage(tag: str):
    find = pages.find_one({"tag": tag})
    if find is not None:
        access.delete_many({'page_id': find['page_id']})
        pages.delete_one({"tag": tag})


def deleteFile(tag, filename):
    find = pages.find_one({'tag': tag})
    if find is not None:
        new_files = list(filter(lambda x: x['filename'] != filename, find['files']))
        pages.update_one({'tag': tag}, {'$set': {'files': new_files}})


def editPage(
        tag: str,
        title: str,
        description: str,
        keywords: str,
        body: str,
        files: [],
        read_users: [],
        write_users: [],
):
    old_page = findPage(tag)
    new_files = [
        {'filename': file.filename, 'content': file.read()}
        for file in filter(lambda x: x.filename != '', files)
    ]
    new_files = new_files + old_page['files']
    pages.update_one(
        {'tag': tag},
        {
            '$set':
                {
                    'title': title,
                    'description': description,
                    'keywords': keywords,
                    'body': body,
                    'files': new_files
                }
        }
    )

    page = findPage(tag)
    page_id = page['page_id']
    access.update_one(
        {'page_id': page_id, 'privilege': Privilage.Read.value},
        {'$set': {'list' : read_users}}
    )
    access.update_one(
        {'page_id': page_id, 'privilege': Privilage.Write.value},
        {'$set': {'list': write_users}}
    )


def validateReadAccess(tag: str, user_id: int) -> bool:
    return validateAccess(tag, user_id, Privilage.Read)


def validateWriteAccess(tag: str, user_id: int) -> bool:
    return validateAccess(tag, user_id, Privilage.Write)


def validateAccess(tag: str, user_id: int, privilage: Privilage) -> bool:
    findP = pages.find_one({'tag': tag})
    page_id = findP['page_id']
    findA = access.find_one({'page_id': page_id, 'privilege': privilage.value})
    return findA is not None and str(user_id) in findA['list']


def getReadUsers(page_id: int) -> [str]:
    findA = access.find_one({'page_id': page_id, 'privilege': Privilage.Read.value})
    return findA['list']


def getWriteUsers(page_id: int) -> [str]:
    findA = access.find_one({'page_id': page_id, 'privilege': Privilage.Write.value})
    return findA['list']
