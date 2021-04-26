import React, {useEffect, useState, useRef} from 'react';

export default function AppWs() {
    const [isPaused, setPause] = useState(false);
    const [messages, setMessages] = useState([]);
    const ws = useRef(null);

    useEffect(() => {
        ws.current = new WebSocket("ws://127.0.0.1:8888/");
        ws.current.onopen = () => console.log("ws opened");
        ws.current.onclose = () => console.log("ws closed");

        return () => {
            ws.current.close();
        };
    }, []);

    useEffect(() => {
        if (!ws.current) return;

        ws.current.onmessage = e => {
            if (isPaused) return;
            setMessages(JSON.parse(e.data));
        };
    }, [isPaused]);

    const fText = (text) => {
      if (typeof text == 'undefined') { return ''; }
      if (text.includes('_')) {
        var list = text.split('_')
        return list[0].replace('CDL', '').replace('-100', '').replace('100', '');
      }
      if (text.includes('.')) {
        var list = text.split('.')
        return list[0] + '.' + list[1].slice(0,4);
      }

      return text
    }

    const tdStyle = {
      textAlign: 'right',
      width: '65px'
    }

    const products = messages.filter((message) => {
      if ('s' in message) {
        return true
      } else {
        return false
      }
      
    }).sort((a, b) => {
      return b.P - a.P;
    }).map((message, i) =>

        <tr key={message.id}>
        
          <td style={tdStyle}>{message.s.replace('USDT', '')}</td>
          <td style={tdStyle}>{fText(message.P)}</td>
          <td style={tdStyle}>{fText(message.c)}</td>
          <td style={tdStyle} className={message['1_sma'] > message.c ? 'red' : 'green'}>{message['1_sma']}</td>
          <td style={tdStyle} className={message['5_sma'] > message.c ? 'red' : 'green'}>{message['5_sma']}</td>
          <td style={tdStyle} className={message['15_sma'] > message.c ? 'red' : 'green'}>{message['15_sma']}</td>
          <td style={tdStyle} className={message['30_sma'] > message.c ? 'red' : 'green'}>{message['30_sma']}</td>
          <td style={tdStyle} className={message['1_is_quality'] === 'True' ? 'green' : ''}>{fText(message['1_target'])}</td>
          <td style={tdStyle} className={message['5_is_quality'] === 'True' ? 'green' : ''}>{fText(message['5_target'])}</td>
          <td style={tdStyle} className={message['15_is_quality'] === 'True' ? 'green' : ''}>{fText(message['15_target'])}</td>
          <td style={tdStyle} className={message['30_is_quality'] === 'True' ? 'green' : ''}>{fText(message['30_target'])}</td>
          <td style={tdStyle}>{fText(message['1_best_battern'])}</td>
          <td style={tdStyle}>{fText(message['5_best_battern'])}</td>
          <td style={tdStyle}>{fText(message['15_best_battern'])}</td>
          <td style={tdStyle}>{fText(message['30_best_battern'])}</td>
        </tr>
    );

    return (

        <div>
          <table>
            <tbody>
            {products}
            </tbody>
          </table>
          <button onClick={() => setPause(!isPaused)}>
            {isPaused ? "Resume" : "Pause"}
          </button>
        </div>
    );
}


  