# https://docs.microsoft.com/en-us/windows/apps/design/shell/tiles-and-notifications/notification-listener
# https://stackoverflow.com/questions/64043297/how-can-i-listen-to-windows-10-notifications-in-python

import asyncio
import json
from pathlib import Path

from aiohttp import ClientSession
from discord import Color, Embed, Webhook
from winrt.windows.ui.notifications import KnownNotificationBindings, NotificationKinds
from winrt.windows.ui.notifications.management import (
    UserNotificationListener,
    UserNotificationListenerAccessStatus,
)

NO_AC_POWER_MSG = "Your UPS battery backup is no longer receiving AC utility power"
AC_POWER_RESTORED_MSG = "AC utility power restored to your battery backup."
PASSED_SELF_TEST_TITLE = "Self-test Passed."
APP_TITLE = "PowerChute System Tray Power Icon"

config = json.loads(Path("config.json").read_text())
SLEEP_TIME_SEC = 60


async def main():
    listener = UserNotificationListener.get_current()

    if (
        await listener.request_access_async()
        != UserNotificationListenerAccessStatus.ALLOWED
    ):
        print("Access to UserNotificationListener is not allowed.")
        exit()
    async with ClientSession() as session:

        webhook = Webhook.from_url(config["webhook_url"], session=session)

        while True:

            notifications = await listener.get_notifications_async(
                NotificationKinds.TOAST
            )

            # for every notification
            for i in range(notifications.size):
                user_notif = notifications.get_at(i)
                app_name = user_notif.app_info.display_info.display_name

                # send whatever the ups notification contained since something is wrong if one was triggered
                if app_name == APP_TITLE:

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

                    # but do filter some messages
                    # self test msgs are spam and not applicable to service status outages
                    if title == PASSED_SELF_TEST_TITLE:
                        listener.remove_notification(user_notif.id)
                        continue

                    # decide message color
                    if title == NO_AC_POWER_MSG:
                        color = Color.red()
                    elif title == AC_POWER_RESTORED_MSG:
                        color = Color.green()
                    else:
                        color = Color.orange()

                    await webhook.send(
                        embed=Embed(
                            title=title, description=message_body, color=color
                        ).set_author(name="APC UPS")
                    )

                    # clear the ups notification so we don't spam
                    listener.remove_notification(user_notif.id)
            await asyncio.sleep(SLEEP_TIME_SEC)


if __name__ == "__main__":
    asyncio.run(main())
