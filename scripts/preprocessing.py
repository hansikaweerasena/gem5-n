import sys

if len(sys.argv) != 3:
    print("Usage: preprocessing.py <no_of_dest> <benchmark>")
    sys.exit(1)

no_of_dest = int(sys.argv[1])
benchmark = sys.argv[2]

gem5_raw_traces = f'{no_of_dest}_{benchmark}_trace.txt'
intermediate_file = f'{no_of_dest}_{benchmark}_inter.txt'
processed_out_file = f'{no_of_dest}_{benchmark}_processed.txt'

print(f'Raw traces file: {gem5_raw_traces}')
print(f'Intermediate file: {intermediate_file}')
print(f'Processed output file: {processed_out_file}')

exclude_types = ['WB_ACK', 'PUTX']

class DataEntry:
    def __init__(self, switch_number, cycle, inOut, resReq, src, srcType, des, memAddr, size, dataType):
        self.switch_number = switch_number
        self.cycle = cycle
        self.inOut = inOut
        self.resReq = resReq
        self.src = src
        self.srcType = srcType
        self.des = des
        self.memAddr = memAddr
        self.size = size
        self.dataType = dataType

    def __repr__(self):
        return f"DataEntry(switch_number={self.switch_number}, cycle={self.cycle}, inOut={self.inOut}, resReq={self.resReq}, src={self.src}, srcType={self.srcType}, des={self.des}, memAddr={self.memAddr}, size={self.size}, dataType={self.dataType})"


class ProcessedMsg:
    def __init__(self, src, dest, size, addr, type):
        self.src = src
        assert len(dest) == 1
        self.dest = dest[0]%no_of_dest
        self.size = size
        self.addr = addr
        self.type = type

    def __repr__(self):
        return f"[src={self.src}, dest={self.dest}, size={self.size}, addr={self.addr}, type={self.type}]"


class ProcessedDataEntry:
    def __init__(self, out_msg, in_msg, delay):
        self.out_msg = out_msg
        self.in_msg = in_msg
        self.delay = delay

    def __repr__(self):
        return f"out_msg={self.out_msg}: in_msg={self.in_msg}: delay={self.delay}"


def getEntry(j, data_entries):
    print(data_entries[j])
    assert data_entries[j].inOut == 'Out'
    outPMsg = ProcessedMsg(data_entries[j].src, data_entries[j].des, data_entries[j].size, data_entries[j].memAddr, data_entries[j].dataType)
    out_cycle = data_entries[j].cycle
    out_swith_no = data_entries[j].switch_number

    while j < len(data_entries) and (data_entries[j].switch_number == out_swith_no):
        j += 1
        if data_entries[j-1].dataType == 'EXCLUSIVE_UNBLOCK':
            break

    inPMsg = ProcessedMsg(data_entries[j-1].src, data_entries[j-1].des, data_entries[j-1].size, data_entries[j-1].memAddr, data_entries[j-1].dataType)
    delay = data_entries[j-1].cycle - out_cycle
    
    #handle EXCLUSIVE_UNBLOCK
    processed_data_entry_2 = None
    if data_entries[j-1].dataType == 'EXCLUSIVE_UNBLOCK':
        while j < len(data_entries) and (data_entries[j].switch_number == out_swith_no):
            j += 1
        inPMsg2 = ProcessedMsg(data_entries[j-1].src, data_entries[j-1].des, data_entries[j-1].size, data_entries[j-1].memAddr, data_entries[j-1].dataType)
        delay2 = data_entries[j-1].cycle - out_cycle
        processed_data_entry_2 = ProcessedDataEntry(outPMsg, inPMsg2, delay2)
    
    return j, ProcessedDataEntry(outPMsg, inPMsg, delay), processed_data_entry_2
    

def parse_line(line):
    try:
        # Extract the PerfectSwitch number and data inside the brackets
        parts = line.split(': {', 1)
        if len(parts) != 2:
            print(f"Unexpected line format: {line}")
            return None
        switch_number = parts[0].split('-')[1].strip()
        data_str = parts[1].rstrip('}\n')
        
        # Initialize an empty dictionary to store parsed data
        data_dict = {}
        
        # Splitting on commas outside of brackets
        bracket_level = 0
        start = 0
        for i, char in enumerate(data_str):
            if char == '[':
                bracket_level += 1
            elif char == ']':
                bracket_level -= 1
            elif char == ',' and bracket_level == 0:
                part = data_str[start:i].strip()
                if part:
                    key, value = part.split(': ', 1)
                    data_dict[key.strip()] = value.strip()
                start = i + 1
        # Add the last or only part
        part = data_str[start:].strip()
        if part:
            key, value = part.split(': ', 1)
            data_dict[key.strip()] = value.strip()
        
        # Convert 'des' to list of integers if present
        des_list = eval(data_dict.get('des', '[]')) # Using eval to directly convert string representation of list to list

        #Convert size to int size
        size_i = 2
        size_s = data_dict.get('size', '')
        if size_s in ['Control', 'Response_Control', 'Writeback_Control']:
            size_i = 2
        elif size_s in ['Response_Data', 'Writeback_Data']:
            size_i = 5
        else:
            print('Unknown size type', size_s)
        
        # Create and return a model object
        return DataEntry(
            switch_number,
            int(data_dict.get('cycle', '0')),
            data_dict.get('inOut', ''),
            data_dict.get('resReq', ''),
            int(data_dict.get('src', '0')),
            data_dict.get('srcType', ''),
            des_list,
            int(data_dict.get('memAddr', '0')),
            size_i,
            data_dict.get('type', '')
        )
    except Exception as e:
        print(f"Error parsing line: {line}. Error: {e}")
        return None


# Read the raw traces and parse them into a list of DataEntry objects

gem5_raw_traces = "wired_data/raw/" + gem5_raw_traces
intermediate_file = "wired_data/intermediate/" + intermediate_file

data_entries = []
with open(gem5_raw_traces, 'r') as file, open(intermediate_file, 'w') as intfile:
    for line in file:
        data_entry = parse_line(line)
        if data_entry.dataType not in exclude_types and not (data_entry.dataType == "EXCLUSIVE_UNBLOCK" and data_entry.inOut=="Out"):
            data_entries.append(data_entry)
            intfile.write(str(data_entry) + '\n')



# Process the data entries into a list of ProcessedDataEntry objects

# find start input message:
i = 0
while data_entries[i].inOut != 'In':
    i += 1
    
initial_processed_data_entry = ProcessedDataEntry(None, ProcessedMsg(data_entries[i].src, data_entries[i].des, data_entries[i].size, data_entries[i].memAddr, data_entries[i].dataType), 0)
i += 1

processed_out_file = "wired_data/processed/" + processed_out_file

with open(processed_out_file, 'w') as outfile:
    outfile.write(str(initial_processed_data_entry) + '\n')
    while i < len(data_entries):
          i, processed_data_entry, second_processed_data_entry = getEntry(i, data_entries)
          outfile.write(str(processed_data_entry) + '\n')
          if second_processed_data_entry:
              print(processed_data_entry)
              print(second_processed_data_entry)
              outfile.write(str(second_processed_data_entry) + '\n')
