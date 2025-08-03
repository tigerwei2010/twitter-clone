import pytest
import time
import threading
from unittest.mock import patch
from snowflake_generator import SnowflakeGenerator


class TestSnowflakeGenerator:

    def test_init_valid_machine_id(self):
        """Test initialization with valid machine ID"""
        generator = SnowflakeGenerator(machine_id=123)
        assert generator.machine_id == 123
        assert generator.sequence == 0
        assert generator.last_timestamp == -1

    def test_init_invalid_machine_id(self):
        """Test initialization with invalid machine ID"""
        with pytest.raises(ValueError):
            SnowflakeGenerator(machine_id=-1)

        with pytest.raises(ValueError):
            SnowflakeGenerator(machine_id=1024)

    def test_generate_id_basic(self):
        """Test basic ID generation"""
        generator = SnowflakeGenerator(machine_id=1)
        snowflake_id = generator.generate_id()

        assert isinstance(snowflake_id, int)
        assert snowflake_id > 0

    def test_generate_unique_ids(self):
        """Test that generated IDs are unique"""
        generator = SnowflakeGenerator(machine_id=1)
        ids = set()

        for _ in range(5000):  # number of ids should be larger than 4096
            snowflake_id = generator.generate_id()
            assert snowflake_id not in ids
            ids.add(snowflake_id)

    def test_generate_ids_sequential(self):
        """Test that IDs are generally increasing"""
        generator = SnowflakeGenerator(machine_id=1)
        prev_id = generator.generate_id()

        for _ in range(5000):
            current_id = generator.generate_id()
            assert current_id > prev_id
            prev_id = current_id

    def test_sequence_increment_same_timestamp(self):
        """Test sequence increment when timestamp is the same"""
        generator = SnowflakeGenerator(machine_id=1)

        # Mock timestamp to return the same value
        fixed_timestamp = int(time.time() * 1000)
        with patch.object(generator, '_current_timestamp', return_value=fixed_timestamp):
            id1 = generator.generate_id()
            id2 = generator.generate_id()

            parsed1 = generator.parse_id(id1)
            parsed2 = generator.parse_id(id2)

            assert parsed1['timestamp'] == parsed2['timestamp']
            assert parsed2['sequence'] == parsed1['sequence'] + 1

    def test_sequence_reset_new_timestamp(self):
        """Test sequence resets on new timestamp"""
        generator = SnowflakeGenerator(machine_id=1)

        # Generate first ID
        timestamp1 = int(time.time() * 1000)
        with patch.object(generator, '_current_timestamp', return_value=timestamp1):
            id1 = generator.generate_id()

        # Generate second ID with different timestamp
        timestamp2 = timestamp1 + 1
        with patch.object(generator, '_current_timestamp', return_value=timestamp2):
            id2 = generator.generate_id()

        parsed1 = generator.parse_id(id1)
        parsed2 = generator.parse_id(id2)

        assert parsed2['timestamp'] > parsed1['timestamp']
        assert parsed2['sequence'] == 0

    def test_clock_backwards_exception(self):
        """Test exception when clock moves backwards"""
        generator = SnowflakeGenerator(machine_id=1)

        # Generate first ID
        timestamp1 = int(time.time() * 1000)
        with patch.object(generator, '_current_timestamp', return_value=timestamp1):
            generator.generate_id()

        # Try to generate with earlier timestamp
        timestamp2 = timestamp1 - 1
        with patch.object(generator, '_current_timestamp', return_value=timestamp2):
            with pytest.raises(Exception, match="Clock moved backwards"):
                generator.generate_id()

    def test_parse_id_components(self):
        """Test parsing ID into components"""
        generator = SnowflakeGenerator(machine_id=123)
        snowflake_id = generator.generate_id()

        parsed = generator.parse_id(snowflake_id)

        assert parsed['id'] == snowflake_id
        assert parsed['machine_id'] == 123
        assert isinstance(parsed['timestamp'], int)
        assert isinstance(parsed['sequence'], int)
        assert isinstance(parsed['datetime'], str)
        assert parsed['sequence'] >= 0
        assert parsed['sequence'] <= 4095

    def test_parse_id_timestamp_accuracy(self):
        """Test parsed timestamp is accurate"""
        generator = SnowflakeGenerator(machine_id=1)

        before_time = int(time.time() * 1000)
        snowflake_id = generator.generate_id()
        after_time = int(time.time() * 1000)

        parsed = generator.parse_id(snowflake_id)

        # Timestamp should be within the time window
        assert before_time <= parsed['timestamp'] <= after_time

    def test_different_machine_ids(self):
        """Test IDs from different machines are different"""
        gen1 = SnowflakeGenerator(machine_id=1)
        gen2 = SnowflakeGenerator(machine_id=2)

        # Generate IDs at same time
        fixed_timestamp = int(time.time() * 1000)
        with patch.object(gen1, '_current_timestamp', return_value=fixed_timestamp), \
             patch.object(gen2, '_current_timestamp', return_value=fixed_timestamp):
            id1 = gen1.generate_id()
            id2 = gen2.generate_id()

        parsed1 = gen1.parse_id(id1)
        parsed2 = gen2.parse_id(id2)

        assert parsed1['machine_id'] == 1
        assert parsed2['machine_id'] == 2
        assert id1 != id2

    def test_thread_safety(self):
        """Test thread safety of ID generation"""
        generator = SnowflakeGenerator(machine_id=1)
        ids = set()
        lock = threading.Lock()

        def generate_ids():
            for _ in range(100):
                snowflake_id = generator.generate_id()
                with lock:
                    assert snowflake_id not in ids
                    ids.add(snowflake_id)

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=generate_ids)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(ids) == 1000  # 10 threads * 100 IDs each

    def test_sequence_overflow(self):
        """Test sequence overflow handling"""
        generator = SnowflakeGenerator(machine_id=1)

        # Set sequence near max
        generator.sequence = 4094
        fixed_timestamp = int(time.time() * 1000)
        generator.last_timestamp = fixed_timestamp

        # Mock to return same timestamp for first call, then next millisecond
        timestamp_calls = [fixed_timestamp, fixed_timestamp, fixed_timestamp + 1]
        call_index = 0
        
        def mock_timestamp():
            nonlocal call_index
            result = timestamp_calls[call_index] if call_index < len(timestamp_calls) else timestamp_calls[-1]
            call_index += 1
            return result

        with patch.object(generator, '_current_timestamp', side_effect=mock_timestamp):
            id1 = generator.generate_id()  # sequence = 4095
            id2 = generator.generate_id()  # sequence = 0, new timestamp

        parsed1 = generator.parse_id(id1)
        parsed2 = generator.parse_id(id2)

        assert parsed1['sequence'] == 4095
        assert parsed2['sequence'] == 0
        assert parsed2['timestamp'] > parsed1['timestamp']

    def test_epoch_calculation(self):
        """Test epoch is correctly set to January 1, 2025"""
        generator = SnowflakeGenerator()

        # January 1, 2025 00:00:00 UTC = 1735689600000 milliseconds
        assert generator.EPOCH == 1735689600000

        # Test with known timestamp
        known_timestamp = 1735689600000 + 1000  # 1 second after epoch
        snowflake_id = (1000 << generator.TIMESTAMP_SHIFT) | (
            0 << generator.MACHINE_ID_SHIFT) | 0

        parsed = generator.parse_id(snowflake_id)
        assert parsed['timestamp'] == known_timestamp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
