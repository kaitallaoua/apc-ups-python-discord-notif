# https://docs.microsoft.com/en-us/windows/apps/design/shell/tiles-and-notifications/notification-listener
# https://stackoverflow.com/questions/64043297/how-can-i-listen-to-windows-10-notifications-in-python
# https://python.plainenglish.io/python-discord-bots-formatting-text-efca0c5dc64a

import asyncio
import json
from pathlib import Path
from time import sleep

from discord import Color, Embed, RequestsWebhookAdapter, Webhook
from winrt.windows.ui.notifications import KnownNotificationBindings, NotificationKinds
from winrt.windows.ui.notifications.management import (
    UserNotificationListener,
    UserNotificationListenerAccessStatus,
)

NO_AC_POWER_MSG = "Your UPS battery backup is no longer receiving AC utility power"
AC_POWER_RESTORED_MSG = "AC utility power restored to your battery backup."
APP_TITLE = "PowerChute System Tray Power Icon"

config = json.loads(Path("config.json").read_text())
WEBHOOK_URL = config["api_url"]
SLEEP_TIME_SEC = 10


async def main():
    listener = UserNotificationListener.get_current()

    if (
        await listener.request_access_async()
        != UserNotificationListenerAccessStatus.ALLOWED
    ):
        print("Access to UserNotificationListener is not allowed.")
        exit()

    webhook = Webhook.from_url(
        WEBHOOK_URL,
        adapter=RequestsWebhookAdapter(),
    )

    while True:

        notifications = await listener.get_notifications_async(NotificationKinds.TOAST)

        # for every notification
        for i in range(notifications.size):
            user_notif = notifications.get_at(i)
            app_name = user_notif.app_info.display_info.display_name

            if app_name == APP_TITLE:

                # send whatever the ups notification contained since something is wrong if one was triggered
                text_elements = user_notif.notification.visual.get_binding(
                    KnownNotificationBindings.get_toast_generic()
                ).get_text_elements()

                title = text_elements.get_at(0).text
                message_body = " ".join(
                    [
                        text_elements.get_at(i + 1).text
                        for i in range(text_elements.size - 1)
                    ]
                )

                # decide message color
                if title == NO_AC_POWER_MSG:
                    color = Color.red()
                elif title == AC_POWER_RESTORED_MSG:
                    color = Color.green()
                else:
                    color = Color.orange()

                embed = Embed(title=title, description=message_body, color=color)
                embed.set_author(name="APC UPS")
                webhook.send(embed=embed)

                # clear the ups notification so we don't spam
                listener.remove_notification(user_notif.id)
        sleep(SLEEP_TIME_SEC)


if __name__ == "__main__":
    asyncio.run(main())
