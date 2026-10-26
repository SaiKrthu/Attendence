import streamlit as st
import pandas as pd
import time 
from datetime import datetime
from pathlib import Path

ts=time.time()
date=datetime.fromtimestamp(ts).strftime("%d-%m-%Y")
timestamp=datetime.fromtimestamp(ts).strftime("%H:%M-%S")

from streamlit_autorefresh import st_autorefresh

count = st_autorefresh(interval=2000, limit=100, key="fizzbuzzcounter")

if count == 0:
    st.write("Count is zero")
elif count % 3 == 0 and count % 5 == 0:
    st.write("FizzBuzz")
elif count % 3 == 0:
    st.write("Fizz")
elif count % 5 == 0:
    st.write("Buzz")
else:
    st.write(f"Count: {count}")


attendance_file = Path(__file__).resolve().parent / "Attendance" / f"Attendance_{date}.csv"
if attendance_file.exists():
    df = pd.read_csv(attendance_file)
    st.dataframe(df.style.highlight_max(axis=0))
else:
    st.info(f"No attendance has been recorded for {date}.")
    st.dataframe(pd.DataFrame(columns=["NAME", "TIME"]))