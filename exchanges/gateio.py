from typing import Any, List, Tuple, Iterator, Optional, Generic, TypeVar
import pandas as pd

def simulate_price_movment_in_markets() -> (
    Iterator[float]
):  # Generator[Tuple[float,float]]:
    "This is a generator object donot return any values"

    df = read_csv("./VANRYUSDT-5m-2024-02-17.csv")
    for _, row in df.iterrows():
        yield float(row["low"])
        yield float(row["high"])



def read_csv(name: str) -> pd.DataFrame:
    col_names: List = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_volume",
        "count",
        "taker_buy_volume",
        "taker_buy_quote_volume",
        "ignore",
    ]
    df = pd.read_csv(name, names=col_names)
    return df

