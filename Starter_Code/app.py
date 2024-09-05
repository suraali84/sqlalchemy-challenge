import numpy as np
import pandas as pd
import datetime as dt
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from flask import Flask, jsonify

# Database Setup
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)

Measurement = Base.classes.measurement
Station = Base.classes.station

# Flask Setup
app = Flask(__name__)

# Utility functions
def get_session():
    return Session(engine)

def get_last_date():
    with get_session() as session:
        return session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]

def get_date_year_ago(date):
    return dt.datetime.strptime(date, '%Y-%m-%d') - dt.timedelta(days=365)

# Flask Routes
@app.route("/")
def homepage():
    """List all available routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the precipitation data for the last 12 months"""
    with get_session() as session:
        last_date = get_last_date()
        one_year_ago = get_date_year_ago(last_date)
        
        results = session.query(Measurement.date, Measurement.prcp).\
            filter(Measurement.date >= one_year_ago).all()
        
        precipitation_dict = {date: prcp for date, prcp in results}
        
    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    """Return a list of stations."""
    with get_session() as session:
        results = session.query(Station.station).all()
        stations_list = list(np.ravel(results))
    
    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    """Return temperature observations for previous year"""
    with get_session() as session:
        most_active_station = session.query(Measurement.station).\
            group_by(Measurement.station).\
            order_by(func.count(Measurement.station).desc()).first()[0]
        
        last_date = session.query(Measurement.date).\
            filter(Measurement.station == most_active_station).\
            order_by(Measurement.date.desc()).first()[0]
        
        one_year_ago = get_date_year_ago(last_date)
        
        results = session.query(Measurement.date, Measurement.tobs).\
            filter(Measurement.station == most_active_station).\
            filter(Measurement.date >= one_year_ago).all()
        
        tobs_list = [{"date": date, "temperature": tobs} for date, tobs in results]
    
    return jsonify(tobs_list)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temp_range(start, end=None):
    """Return TMIN, TAVG, and TMAX for a date range."""
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
    
    with get_session() as session:
        if not end:
            results = session.query(*sel).filter(Measurement.date >= start).all()
        else:
            results = session.query(*sel).\
                filter(Measurement.date >= start).\
                filter(Measurement.date <= end).all()
    
    temp_stats = list(np.ravel(results))
    
    return jsonify({
        "TMIN": temp_stats[0],
        "TAVG": temp_stats[1],
        "TMAX": temp_stats[2]
    })

if __name__ == '__main__':
    app.run(debug=True)