"""
Transaction Wrapper Utility for MongoDB
Ensures atomic operations for critical database updates
"""
import logging
from typing import Callable, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession
from contextlib import asynccontextmanager

logger = logging.getLogger("transaction")


@asynccontextmanager
async def get_transaction_session(client: AsyncIOMotorClient):
    """
    Context manager for MongoDB transaction sessions.

    Usage:
        async with get_transaction_session(client) as session:
            await collection.update_one({...}, {...}, session=session)
            await collection.insert_one({...}, session=session)
    """
    session = await client.start_session()
    try:
        async with session.start_transaction():
            yield session
            # Transaction commits automatically if no exception
    except Exception as e:
        # Transaction aborts automatically on exception
        logger.error(f"Transaction aborted due to error: {e}")
        raise
    finally:
        await session.end_session()


async def with_transaction(
    client: AsyncIOMotorClient,
    callback: Callable[[AsyncIOMotorClientSession], Any]
) -> Any:
    """
    Execute a function within a MongoDB transaction.
    Automatically commits on success, aborts on error.

    Args:
        client: MongoDB client instance
        callback: Async function to execute within transaction.
                 Must accept session as first parameter.

    Returns:
        Result from callback function

    Raises:
        Any exception raised by callback

    Example:
        async def update_credits(session):
            await db.users.update_one(
                {"_id": user_id},
                {"$inc": {"credits": amount}},
                session=session
            )
            await db.credit_logs.insert_one({...}, session=session)
            return True

        result = await with_transaction(mongo_client, update_credits)
    """
    session = await client.start_session()

    try:
        async with session.start_transaction():
            result = await callback(session)
            # Transaction commits automatically here
            logger.debug("Transaction committed successfully")
            return result

    except Exception as e:
        # Transaction aborts automatically on exception
        logger.error(f"Transaction failed and was aborted: {e}", exc_info=True)
        raise

    finally:
        await session.end_session()


class TransactionManager:
    """
    Transaction manager for easier transaction handling.
    Provides both context manager and functional interfaces.
    """

    def __init__(self, client: AsyncIOMotorClient):
        self.client = client

    @asynccontextmanager
    async def session(self):
        """
        Get a transaction session as a context manager.

        Usage:
            tx_manager = TransactionManager(mongo_client)
            async with tx_manager.session() as session:
                await db.users.update_one({...}, {...}, session=session)
        """
        async with get_transaction_session(self.client) as session:
            yield session

    async def execute(self, callback: Callable[[AsyncIOMotorClientSession], Any]) -> Any:
        """
        Execute a callback within a transaction.

        Usage:
            tx_manager = TransactionManager(mongo_client)

            async def do_payment(session):
                await db.users.update_one({...}, {...}, session=session)
                await db.payments.insert_one({...}, session=session)

            result = await tx_manager.execute(do_payment)
        """
        return await with_transaction(self.client, callback)

    async def execute_batch(self, callbacks: list[Callable[[AsyncIOMotorClientSession], Any]]) -> list[Any]:
        """
        Execute multiple callbacks within a single transaction.
        All callbacks share the same transaction session.

        Args:
            callbacks: List of async functions to execute

        Returns:
            List of results from each callback
        """
        async def batch_callback(session):
            results = []
            for callback in callbacks:
                result = await callback(session)
                results.append(result)
            return results

        return await with_transaction(self.client, batch_callback)


# Decorator for automatic transaction handling
def transactional(func):
    """
    Decorator to automatically wrap a function in a transaction.

    Note: The decorated function must accept 'session' as a keyword argument.
    The client must be passed as the first argument or 'client' keyword arg.

    Usage:
        @transactional
        async def update_user_credits(client, user_id, amount, *, session=None):
            await client.truebond.users.update_one(
                {"_id": user_id},
                {"$inc": {"credits": amount}},
                session=session
            )

        await update_user_credits(mongo_client, user_id, 100)
    """
    async def wrapper(*args, **kwargs):
        # Extract client from args or kwargs
        client = None
        if args and hasattr(args[0], 'start_session'):
            client = args[0]
        elif 'client' in kwargs:
            client = kwargs['client']

        if not client:
            raise ValueError("Client must be provided as first argument or 'client' kwarg")

        # Check if session already provided (nested transaction)
        if kwargs.get('session'):
            # Already in a transaction, just execute
            return await func(*args, **kwargs)

        # Create new transaction
        async def callback(session):
            kwargs['session'] = session
            return await func(*args, **kwargs)

        return await with_transaction(client, callback)

    return wrapper


# Helper function for Beanie ODM
async def with_beanie_transaction(callback: Callable[[AsyncIOMotorClientSession], Any]) -> Any:
    """
    Execute a function within a transaction using Beanie's client.

    Note: Requires that Beanie has been initialized.

    Usage:
        from backend.models.tb_user import TBUser

        async def update_user(session):
            user = await TBUser.get(user_id, session=session)
            user.credits += 100
            await user.save(session=session)

        await with_beanie_transaction(update_user)
    """
    from beanie import get_motor_client

    client = get_motor_client()
    if not client:
        raise RuntimeError("Beanie client not initialized. Call init_beanie() first.")

    return await with_transaction(client, callback)
