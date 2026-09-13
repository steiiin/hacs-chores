/* UI fixture only; these mutations never reach Home Assistant. */
(async () => {
  const data = await (await fetch('demo-data.json')).json();
  const listeners = new Set();
  const history = new Map();
  const publish = () => listeners.forEach(listener => listener(structuredClone(data)));
  const hass = {
    connection:{subscribeMessage:async callback => {listeners.add(callback);queueMicrotask(publish);return () => listeners.delete(callback);}},
    callWS:async message => {
      if (document.querySelector('#fail').checked) throw new Error('Beispiel: Speichern fehlgeschlagen. Es wurde nichts gebucht.');
      if (message.type === 'hacs_chores/complete') {
        const task = data.tasks.find(t => t.id === message.task_id);
        if (!task.is_due || task.due_at !== message.due_at) throw new Error('Dieser Termin wurde bereits erledigt.');
        const member = data.members.find(m => m.id === message.member_id);
        const completion_id = crypto.randomUUID();
        history.set(completion_id, structuredClone(data));
        task.is_due = false; task.last_done = data.now; task.last_member_name = member.name;
        task.due_at = '2026-09-12T06:00:00+00:00';
        const stats = data.statistics.find(m => m.id === member.id);
        stats.minutes += task.effort_minutes; stats.count += 1; data.total_minutes += task.effort_minutes;
        const item = stats.tasks.find(t => t.title === task.title);
        if (item) {item.count++;item.minutes += task.effort_minutes;} else stats.tasks.push({title:task.title,count:1,minutes:task.effort_minutes});
        stats.tasks.sort((a,b) => b.count-a.count);
        data.statistics.forEach(m => {m.share=Math.round(m.minutes/data.total_minutes*1000)/10;});
        data.statistics.sort((a,b) => b.minutes-a.minutes);
        publish();return {completion_id};
      }
      Object.assign(data, history.get(message.completion_id)); publish(); return {};
    },
  };
  document.querySelectorAll('hacs-chores-card,hacs-chores-stats-card,hacs-chores-quick-card').forEach(card => {card.setConfig({});card.hass=hass;});
  let dark = false;
  document.querySelector('#dark').onclick = () => {
    dark = !dark;
    const values = dark ? {'--primary-text-color':'#e4eadf','--secondary-text-color':'#b0bca9','--card-background-color':'#26372e','--secondary-background-color':'#304639','--divider-color':'#4d6052'} : {};
    document.documentElement.removeAttribute('style');
    Object.entries(values).forEach(([key,value]) => document.documentElement.style.setProperty(key,value));
  };
})();
