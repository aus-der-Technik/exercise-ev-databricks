from datetime import timedelta, datetime

from generator import *
import random
from time import sleep

sleep_time = 1

TRANSACTION_CACHE = 0


def _generate_config(charge_point_id: str, base_time: datetime, num_transactions: int) -> Dict:
    return {
        "charge_point_id": charge_point_id,
        "connector_id": random.randint(1, 5),
        "rfid": str(random.getrandbits(64)),
        "base_time": base_time,
        "num_transactions": num_transactions
    }

def _update_body_with_timestamp(body: Dict, update_func: Callable, new_datetime: datetime) -> Dict:
    timestamp_data = update_func(new_datetime.isoformat())
    return body | timestamp_data

def _decorate(charge_point_id: str, action: str, body: Dict, timestamp: datetime) -> Dict:
    data = {
        "charge_point_id": charge_point_id,
        "write_timestamp": timestamp.isoformat(),
        "action": action,
        "body": body
    }
    print(data)
    return data


def create_transaction(connector_id: int, rfid: str):
    transactions_start = [
        create_start_transaction(connector_id=connector_id, rfid=rfid)
    ]

    charge_duration = random.randint(3, 25)
    current_meter_values = None
    transaction_ongoing = [create_meter_values(transaction_id=TRANSACTION_CACHE, connector_id=x["connector_id"],
                                               current_meter_values=current_meter_values) for i in
                           range(charge_duration)]

    last_meter_reading = list(filter(lambda x: x["measurand"] in [Measurand.energy_active_import_register],
                                     transaction_ongoing[-1][0]["meter_value"][0]["sampled_value"]))

    transaction_stop = [
        create_stop_transaction(transaction_id=TRANSACTION_CACHE, rfid=x["rfid"],
                                meter_stop_wh=last_meter_reading[0]["value"])
    ]

    return transactions_start + transaction_ongoing + transaction_stop


charge_point_ids = [
    {
        "charge_point_id": "AL1000",
        "base_time": datetime(2022, 10, 2, 15, 16, 17, 345, tzinfo=pytz.utc),
        "num_transactions": 2
    },
    {
        "charge_point_id": "AL1000",
        "base_time": datetime(2022, 10, 2, 23, 50, 23, 337, tzinfo=pytz.utc),
        "num_transactions": 4
    },
    {
        "charge_point_id": "AL2000",
        "base_time": datetime(2022, 10, 2, 23, 47, 35, 254, tzinfo=pytz.utc),
        "num_transactions": 6
    },
    {
        "charge_point_id": "AL3000",
        "base_time": datetime(2022, 12, 11, 4, 15, 47, 236, tzinfo=pytz.utc),
        "num_transactions": 5
    },
    {
        "charge_point_id": "AL4000",
        "base_time": datetime(2022, 12, 5, 6, 13, 55, 432, tzinfo=pytz.utc),
        "num_transactions": 4
    },
    {
        "charge_point_id": "AL5000",
        "base_time": datetime.now(tz=pytz.utc),
        "num_transactions": 6
    },
]


def time_tick_value(tick: int):
    return timedelta(seconds=120*tick)

for x in list(map(lambda x: _generate_config(**x), charge_point_ids)):

    base = [
        create_boot_notification(charge_point_id=x["charge_point_id"]),
    ] + [ create_heartbeat() for i in range(random.randint(1,10))]


    transactions_list = []
    for i in range(x["num_transactions"]):
        TRANSACTION_CACHE += 1
        new_transactions = create_transaction(connector_id=x["connector_id"], rfid=x["rfid"])
        transactions_list = transactions_list + new_transactions

    all_messages = base + transactions_list
    current_time = x["base_time"]
    result = []
    for idx, r in enumerate(all_messages):
        new_datetime = current_time+time_tick_value(idx)
        result = result + [
            _decorate(
                charge_point_id=x["charge_point_id"],
                action=r[1],
                body=_update_body_with_timestamp(body=r[0], update_func=r[2], new_datetime=new_datetime),
                timestamp=new_datetime
            )]