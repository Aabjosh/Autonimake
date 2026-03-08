# this file provides the methods which correspond to sending data from each standard device type

def getMessage(datatype, message):

    # these match the JSON, and so do the following functions
    function_calls = {
        "TWO_DIRECTIONAL_DIGITAL": return_LR_digital,
        "CHARACTER_STREAM": return_text
    }

    output = function_calls[datatype](message) # calls the right function for the API key
    return output

def return_LR_digital(message):

    # left and right both high
    match message:
        case "FORWARD":
            return "1,1"
        case "LEFT":
            return "-1,1"
        case "RIGHT":
            return "1,-1"
        case "STOP":
            return "0,0"
        
def return_text(message):
    return message