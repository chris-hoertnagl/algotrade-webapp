from django import template
import datetime

register = template.Library()


def print_timestamp(timestamp):
    try:
        # assume, that timestamp is given in seconds with decimal point
        ts = float(timestamp / 1000)
    except ValueError:
        return None
    return datetime.datetime.fromtimestamp(ts)


register.filter(print_timestamp)


# def reverse_list(input_list: list):
#     if not input_list:
#         return input_list
#     else:
#         input_list.reverse()
#         length = len(input_list)
#         if length > 5:
#             input_list = input_list[:5]
#         return input_list
#
#
# register.filter(reverse_list)
