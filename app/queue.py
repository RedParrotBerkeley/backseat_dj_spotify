# app/queue.py
# Simple in-memory FIFO queue
deque = []

def append(item):
    deque.append(item)

def pop(index=0):
    return deque.pop(index) if deque else None

def __len__():
    return len(deque)

def __iter__():
    return iter(deque)

def __getitem__(index):
    return deque[index]

def __contains__(item):
    return item in deque

request_queue = deque
