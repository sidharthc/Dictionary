import unittest
import hipappear
import mock
from hipappear import main, app

message_data = {"item": {
                          "message": {
                                      "from": {
                                               "name": "abc"
                                               },
                                      "message": "/appear",
                                      },
                          "room": {
                                   "name": "test_data",
                                   "id": "1234"
                                   }
                          },
                 "oauth_client_id": "test-4e2c",
                }

tenant_id = 1234
message_text = "Join abc's <a href = 'https://appear.in/room'>appear.in conference</a>."
error_message = ("To start <a href='" + app.config['APPEAR_URL'] + "'>" +
                 "appear.in</a> video conference, just type \"/appear\".")


class FlaskrTestCase(unittest.TestCase):

    def test_notification_message(self):
        #Mocking the response of api cal to appear
        main.get_appear_random_room_name = mock.Mock(return_value='/room')
        #Checking the message when command is '/appear'
        message = main.generate_notification_message(message_data)
        self.assertEqual(message, message_text)
        #Checking the message when command is '/appear  '
        message_data['item']['message']['message'] = "/appear  "
        message = main.generate_notification_message(message_data)
        self.assertEqual(message, message_text)
        #Checking the message when command is '/appear abcd'
        message_data['item']['message']['message'] = "/appear abcd"
        message = main.generate_notification_message(message_data)
        self.assertEqual(message, error_message)


def get_unique_room_name(message):
    unique_message = message[-33:]
    return unique_message[0:12]

if __name__ == '__main__':
    unittest.main()
