// Create candlestick chart from lightweight charts lib
var chart = LightweightCharts.createChart(document.getElementById('chart'), {
    width: document.getElementById("chart").offsetWidth,
    height: 400,
    layout: {
        backgroundColor: '#191B20',
        textColor: 'rgba(255, 255, 255, 0.9)',
    },
    grid: {
        vertLines: {
            color: 'rgba(197, 203, 206, 0.5)',
        },
        horzLines: {
            color: 'rgba(197, 203, 206, 0.5)',
        },
    },
    crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal,
    },
    priceScale: {
        borderColor: 'rgba(197, 203, 206, 0.8)',
    },
    timeScale: {
        borderColor: 'rgba(197, 203, 206, 0.8)',
        timeVisible: true,
        secondsVisible: false,
    },
});

var candleSeries = chart.addCandlestickSeries({
    upColor: '#02C076',
    downColor: '#D0304A',
});

// get current symbol to connect to current websocket
var symbol = document.getElementById("symbol").value.toLowerCase();
var binanceSocket = new WebSocket(`wss://stream.binance.com:9443/ws/${symbol}@kline_1m`);

// check if there is any relevant price data in session storage
if (sessionStorage.getItem("candleList") != null && sessionStorage.getItem("symbol") === symbol) {
    console.log("sessionStorage used to fill candle chart")
    candleArr = []
    let candleList = sessionStorage.getItem("candleList");
    candleList = JSON.parse(candleList)
    candleList.forEach(function (candleEntry) {
        candleArr.push(candleEntry)
        candleSeries.update(candleEntry)
    })
} else {
    console.log("sessionStorage empty or symbol changed")
    sessionStorage.clear()
    sessionStorage.setItem("symbol", symbol)
    candleArr = []
}

//
binanceSocket.onmessage = function (event) {
    let message = JSON.parse(event.data);
    let candlestick = message.k;

    if (candlestick.x) {
        let j_candle = {
            time: candlestick.t / 1000,
            open: candlestick.o,
            high: candlestick.h,
            low: candlestick.l,
            close: candlestick.c
        };
        candleArr.push(j_candle);
        sessionStorage.setItem("candleList", JSON.stringify(candleArr));
    }

    candleSeries.update({
        time: candlestick.t / 1000,
        open: candlestick.o,
        high: candlestick.h,
        low: candlestick.l,
        close: candlestick.c
    })
}