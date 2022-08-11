class DataFormat(Exception):
    pass
class DataType(Exception):
    pass
class DataError(Exception):
    pass
class UUIDError(Exception):
    pass
class UUIDNotFound(Exception):
    res = {}
    res['status'] = 'NOT_FOUND'
    res['message'] = 'No event found with given id'
    
class RecordNotFound(Exception):
    pass
class IDNotFound(Exception):
    pass
class CategoryError(Exception):
    pass
class MoreThanOneRecordReturned(Exception):
    pass
class Duplicate(Exception):
    pass
class EventConflict(Exception):
    pass
class BlockedEventTitle(Exception):
    pass
class SaveImageError(Exception):
    pass

class UnknownError(Exception):
    res = {}
    res['status'] = 'ERROR'
    res['message'] = 'Unknown error ocurred. Please See log for details'
    

