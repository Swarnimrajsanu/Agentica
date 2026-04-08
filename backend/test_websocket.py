"""
WebSocket Test Client for Agentica
Shows real-time simulation streaming
"""
import asyncio
import websockets
import json
from loguru import logger


async def test_live_simulation():
    """
    Test the MOST IMPRESSIVE WebSocket endpoint!
    Connects and watches simulation happen in real-time
    """
    topic = "Should_I_launch_AI_product_in_2024"
    uri = f"ws://localhost:8000/api/ws/simulate/{topic}"
    
    logger.info(f"Connecting to {uri}")
    logger.info("=" * 60)
    
    async with websockets.connect(uri) as websocket:
        logger.info("✅ Connected to WebSocket!")
        logger.info("=" * 60)
        
        # Receive and print messages
        message_count = 0
        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                message_count += 1
                
                # Format output based on message type
                msg_type = data.get("type", "unknown")
                
                if msg_type == "connected":
                    logger.info(f"🔗 {data['message']}")
                    logger.info(f"   Client ID: {data.get('client_id')}")
                
                elif msg_type == "simulation_starting":
                    logger.info(f"\n🚀 {data['message']}")
                    logger.info(f"   Topic: {data.get('topic')}")
                
                elif msg_type == "agents_spawned":
                    logger.info(f"\n✨ {data['message']}")
                    agents = data.get('agents', [])
                    for i, agent in enumerate(agents, 1):
                        logger.info(f"   {i}. {agent['role']}")
                
                elif msg_type == "simulation_start":
                    logger.info(f"\n🎬 Simulation Started")
                    logger.info(f"   ID: {data.get('simulation_id')}")
                    logger.info(f"   Topic: {data.get('topic')}")
                
                elif msg_type == "round_start":
                    logger.info(f"\n{'='*60}")
                    logger.info(f"📍 ROUND {data.get('round')}/{data.get('total_rounds')}")
                    logger.info(f"{'='*60}")
                
                elif msg_type == "agent_response":
                    msg = data.get('message', {})
                    agent_role = msg.get('agent_role', 'Unknown')
                    content = msg.get('content', '')
                    round_num = msg.get('round', 0)
                    
                    logger.info(f"\n💬 [{agent_role}] (Round {round_num}):")
                    logger.info(f"   {content}")
                
                elif msg_type == "round_end":
                    logger.info(f"\n✅ Round {data.get('round')} completed")
                
                elif msg_type == "simulation_complete":
                    logger.info(f"\n{'='*60}")
                    logger.info(f"🎉 {data['message']}")
                    result = data.get('result', {})
                    logger.info(f"   Messages: {result.get('messages_count')}")
                    logger.info(f"   Consensus: {result.get('consensus', {}).get('consensus', 'N/A')}")
                    logger.info(f"{'='*60}")
                    
                    # Close after completion
                    await websocket.send(json.dumps({"type": "close"}))
                    break
                
                elif msg_type == "error":
                    logger.error(f"❌ Error: {data.get('message')}")
                    break
        
        except websockets.exceptions.ConnectionClosed:
            logger.info("\n🔌 Connection closed")
    
    logger.info(f"\n✅ Total messages received: {message_count}")


async def test_manual_subscription():
    """
    Test manual subscription to simulation updates
    """
    uri = "ws://localhost:8000/api/ws"
    
    logger.info(f"Connecting to {uri}")
    
    async with websockets.connect(uri) as websocket:
        # Receive welcome message
        welcome = await websocket.recv()
        logger.info(f"Connected: {welcome}")
        
        # Subscribe to a simulation
        subscription = {
            "type": "subscribe",
            "simulation_id": "sim_Should_I_launch_AI_product_in_2024"
        }
        
        await websocket.send(json.dumps(subscription))
        response = await websocket.recv()
        logger.info(f"Subscription response: {response}")
        
        # Keep connection open to receive updates
        logger.info("Waiting for simulation updates...")
        try:
            for _ in range(10):  # Wait for up to 10 messages
                message = await asyncio.wait_for(websocket.recv(), timeout=30)
                logger.info(f"Update: {message}")
        except asyncio.TimeoutError:
            logger.info("No more updates (timeout)")


if __name__ == "__main__":
    import sys
    
    logger.add("websocket_test.log", rotation="1 MB")
    
    print("\n" + "="*60)
    print("🤖 AGENTICA WEBSOCKET TEST CLIENT")
    print("="*60)
    print("\nChoose test mode:")
    print("1. Live Simulation (Most Impressive!)")
    print("2. Manual Subscription")
    print("="*60)
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        logger.info("Starting LIVE SIMULATION test...")
        asyncio.run(test_live_simulation())
    elif choice == "2":
        logger.info("Starting MANUAL SUBSCRIPTION test...")
        asyncio.run(test_manual_subscription())
    else:
        print("Invalid choice!")
        sys.exit(1)
