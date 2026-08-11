#!/usr/bin/env node

import CartofreakoWorkerClient from '../src.wasm/cartofreako-worker-client.mjs';

function requireCondition(condition, message) {
    if (!condition) throw new Error(message);
}

class FakeWorker {
    listeners = new Map();
    messages = [];
    terminated = false;
    addEventListener(type, callback) { this.listeners.set(type, callback); }
    postMessage(message) { this.messages.push(message); }
    terminate() { this.terminated = true; }
    respond(data) { this.listeners.get('message')?.({data}); }
}

const worker = new FakeWorker();
const client = new CartofreakoWorkerClient({worker});
const controller = new AbortController();
const pending = client.forwardMany({id: 'myriahedral', width: 44},
    new Float64Array([171.2, 7.1]), {signal: controller.signal});
controller.abort(new Error('test cancellation'));
let aborted = false;
try { await pending; } catch (error) { aborted = error.name === 'AbortError'; }
requireCondition(aborted, 'AbortSignal did not reject the worker request');
requireCondition(worker.messages.length === 2
    && worker.messages[0].type === 'forwardMany'
    && worker.messages[1].type === 'cancel'
    && worker.messages[0].requestId === worker.messages[1].requestId,
'worker cancellation message is malformed');
worker.respond({requestId: worker.messages[0].requestId, ok: true, value: 'late'});

const preAborted = new AbortController();
preAborted.abort();
const messageCount = worker.messages.length;
try { await client.manifest({signal: preAborted.signal}); } catch (error) {
    requireCondition(error.name === 'AbortError', 'pre-abort returned the wrong error');
}
requireCondition(worker.messages.length === messageCount,
    'pre-aborted request was posted to the worker');

const manifest = client.manifest();
const requestId = worker.messages.at(-1).requestId;
worker.respond({requestId, ok: true, value: {apiVersion: 3}});
requireCondition((await manifest).apiVersion === 3, 'ordinary worker response failed');
client.terminate();
requireCondition(worker.terminated, 'worker was not terminated');
console.log('worker cancellation passed: pre-abort, queued abort, late-result suppression, ordinary response');
