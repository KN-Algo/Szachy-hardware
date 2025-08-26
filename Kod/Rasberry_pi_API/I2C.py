"""
I2C Move Command Library
========================

A Python library for controlling robotic movement via I2C communication.
Provides functions for sending move commands, connection testing, and homing operations.

Author: Your Name
Version: 1.0.0
"""

import smbus2
import time
import struct


class I2CMoveController:
    """
    I2C Move Controller for robotic systems.
    
    This class provides methods to communicate with robotic devices over I2C,
    including movement commands, homing operations, and connection testing.
    """
    
    def __init__(self, bus_number=1, slave_address=0x42):
        """
        Initialize the I2C Move Controller.
        
        Args:
            bus_number (int): I2C bus number (default: 1)
            slave_address (int): I2C slave device address (default: 0x42)
        """
        self.bus = smbus2.SMBus(bus_number)
        self.slave_addr = slave_address
    
    def send_move_command(self, x_start, y_start, x_end, y_end, timeout=15.0, poll_interval=0.5):
        """
        Send a move command to the robotic device and wait for completion.
        
        This function sends coordinates for a movement from start position to end position,
        then polls the device status until the movement is complete or timeout occurs.
        
        Args:
            x_start (float): Starting X coordinate
            y_start (float): Starting Y coordinate
            x_end (float): Ending X coordinate
            y_end (float): Ending Y coordinate
            timeout (float): Maximum time to wait for completion in seconds (default: 15.0)
            poll_interval (float): Time between status polls in seconds (default: 0.5)
        
        Returns:
            bool: True if movement completed successfully, False otherwise
            
        Raises:
            Exception: If communication error occurs during command transmission
        """
        try:
            # Prepare data (little endian float format)
            command_byte = ord('M')
            data = struct.pack('<ffff', x_start, y_start, x_end, y_end)
            
            # Send command with data
            self.bus.write_i2c_block_data(self.slave_addr, command_byte, list(data))
            
            # Poll for completion
            max_attempts = int(timeout / poll_interval)
            attempt = 0
            start_time = time.time()
            
            while attempt < max_attempts:
                attempt += 1
                time.sleep(poll_interval)
                
                try:
                    response_byte = self.bus.read_byte(self.slave_addr)
                    
                    if response_byte == ord('M'):  # Movement completed
                        return True
                    elif response_byte == ord('W'):  # Work in progress
                        continue
                    elif response_byte == ord('E'):  # Error occurred
                        return False
                    # Continue polling for unexpected responses
                        
                except Exception:
                    # Continue polling on read errors
                    continue
            
            # Timeout occurred
            return False
            
        except Exception as e:
            raise Exception(f"Failed to send move command: {e}")
    
    def test_connection(self):
        """
        Test basic I2C connection to the device.
        
        Attempts to establish communication with the slave device by sending
        a simple byte write operation.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            self.bus.write_byte(self.slave_addr, 0x00)
            return True
        except Exception:
            return False
    
    def perform_homing(self, timeout=30.0, poll_interval=0.5):
        """
        Perform homing operation on the robotic device.
        
        Sends a homing command and waits for completion. Homing typically
        moves the device to its reference/home position and may take considerable time.
        
        Args:
            timeout (float): Maximum time to wait for homing completion in seconds (default: 30.0)
            poll_interval (float): Time between status polls in seconds (default: 0.5)
        
        Returns:
            bool: True if homing completed successfully, False otherwise
            
        Raises:
            Exception: If communication error occurs during homing command transmission
        """
        try:
            # Send homing command
            command_byte = ord('H')
            self.bus.write_byte(self.slave_addr, command_byte)
            
            # Poll for completion
            max_attempts = int(timeout / poll_interval)
            attempt = 0
            
            while attempt < max_attempts:
                attempt += 1
                time.sleep(poll_interval)
                
                try:
                    response_byte = self.bus.read_byte(self.slave_addr)
                    
                    if response_byte == ord('H'):  # Homing completed
                        return True
                    elif response_byte == ord('W'):  # Work in progress
                        continue
                    elif response_byte == ord('E'):  # Error occurred
                        return False
                    # Continue polling for unexpected responses
                        
                except Exception:
                    # Continue polling on read errors
                    continue
            
            # Timeout occurred
            return False
            
        except Exception as e:
            raise Exception(f"Failed to perform homing: {e}")
    
    def get_device_status(self):
        """
        Get current status of the robotic device.
        
        Reads a single status byte from the device and interprets it.
        
        Returns:
            tuple: (status_byte, status_description) where:
                - status_byte (int): Raw status byte received from device
                - status_description (str): Human-readable status description
                
        Raises:
            Exception: If communication error occurs during status read
        """
        try:
            status_byte = self.bus.read_byte(self.slave_addr)
            
            # Interpret status codes
            status_descriptions = {
                ord('M'): 'Movement completed',
                ord('H'): 'Homing completed', 
                ord('W'): 'Work in progress',
                ord('E'): 'Error state',
                ord('I'): 'Idle/Ready'
            }
            
            description = status_descriptions.get(status_byte, f'Unknown status (code: {status_byte})')
            return status_byte, description
            
        except Exception as e:
            raise Exception(f"Failed to read device status: {e}")
    
    def close(self):
        """
        Close the I2C bus connection.
        
        Should be called when finished using the controller to properly
        release the I2C bus resources.
        """
        if hasattr(self, 'bus') and self.bus:
            self.bus.close()


# Convenience functions for backward compatibility and ease of use
def create_controller(bus_number=1, slave_address=0x42):
    """
    Create and return an I2CMoveController instance.
    
    Args:
        bus_number (int): I2C bus number (default: 1)
        slave_address (int): I2C slave device address (default: 0x42)
    
    Returns:
        I2CMoveController: Configured controller instance
    """
    return I2CMoveController(bus_number, slave_address)


# Test and demonstration functions
def run_connection_test(controller=None, verbose=True):
    """
    Test function to verify I2C connection and basic functionality.
    
    This function performs a series of tests including connection verification,
    homing operation, and sample movement commands to validate the system.
    
    Args:
        controller (I2CMoveController, optional): Controller instance to test.
                                                If None, creates a new one.
        verbose (bool): Whether to print detailed test progress (default: True)
    
    Returns:
        dict: Test results containing success status and details for each test
    """
    if controller is None:
        controller = create_controller()
    
    results = {
        'connection': {'success': False, 'details': ''},
        'homing': {'success': False, 'details': ''},
        'movement': {'success': False, 'details': ''},
        'status_read': {'success': False, 'details': ''}
    }
    
    if verbose:
        print("🔍 Starting I2C Move Controller Tests")
        print("=" * 40)
    
    # Test 1: Connection
    if verbose:
        print("1. Testing connection...")
    
    try:
        if controller.test_connection():
            results['connection'] = {'success': True, 'details': 'Connection established successfully'}
            if verbose:
                print("   ✅ Connection OK")
        else:
            results['connection'] = {'success': False, 'details': 'Failed to establish connection'}
            if verbose:
                print("   ❌ Connection failed")
                return results
    except Exception as e:
        results['connection'] = {'success': False, 'details': f'Connection error: {e}'}
        if verbose:
            print(f"   ❌ Connection error: {e}")
        return results
    
    # Test 2: Status reading
    if verbose:
        print("2. Testing status read...")
    
    try:
        status_byte, status_desc = controller.get_device_status()
        results['status_read'] = {'success': True, 'details': f'Status: {status_desc} (code: {status_byte})'}
        if verbose:
            print(f"   ✅ Status read OK: {status_desc}")
    except Exception as e:
        results['status_read'] = {'success': False, 'details': f'Status read error: {e}'}
        if verbose:
            print(f"   ❌ Status read error: {e}")
    
    # Test 3: Homing
    if verbose:
        print("3. Testing homing (may take up to 30 seconds)...")
    
    try:
        if controller.perform_homing(timeout=30.0):
            results['homing'] = {'success': True, 'details': 'Homing completed successfully'}
            if verbose:
                print("   ✅ Homing completed")
        else:
            results['homing'] = {'success': False, 'details': 'Homing timeout or error'}
            if verbose:
                print("   ❌ Homing failed or timeout")
    except Exception as e:
        results['homing'] = {'success': False, 'details': f'Homing error: {e}'}
        if verbose:
            print(f"   ❌ Homing error: {e}")
    
    # Test 4: Sample movement
    if verbose:
        print("4. Testing sample movement...")
    
    try:
        if controller.send_move_command(0.0, 0.0, 10.0, 10.0, timeout=15.0):
            results['movement'] = {'success': True, 'details': 'Sample movement completed successfully'}
            if verbose:
                print("   ✅ Movement completed")
        else:
            results['movement'] = {'success': False, 'details': 'Movement timeout or error'}
            if verbose:
                print("   ❌ Movement failed or timeout")
    except Exception as e:
        results['movement'] = {'success': False, 'details': f'Movement error: {e}'}
        if verbose:
            print(f"   ❌ Movement error: {e}")
    
    if verbose:
        print("\n📋 Test Summary:")
        for test_name, result in results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"   {test_name.capitalize()}: {status}")
        print("=" * 40)
    
    return results


# Example usage and demonstration
if __name__ == "__main__":
    print("I2C Move Controller Library - Test Mode")
    print("=" * 50)
    
    # Create controller instance
    try:
        controller = create_controller()
        
        # Run comprehensive tests
        test_results = run_connection_test(controller, verbose=True)
        
        # Check if all tests passed
        all_passed = all(result['success'] for result in test_results.values())
        
        if all_passed:
            print("\n🎉 All tests PASSED! Library is ready for use.")
        else:
            print("\n⚠️  Some tests FAILED. Check hardware connections and device status.")
        
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        # Clean up
        try:
            controller.close()
        except:
            pass
        print("\n🏁 Test completed")