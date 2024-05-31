import unittest
from codetechnician.command_parser import parse_input, Message, OutputCommand, UpdateCommand, ModelInstruction, PlainTextCommand, FileSelectorCommand, Error

class TestParser(unittest.TestCase):
    def test_output_command(self):
        input_str = " /o Write me a Hello World in C#."
        expected_output = OutputCommand(Message("Write me a Hello World in C#."))
        self.assertEqual(parse_input(input_str), expected_output)

        input_str = "   /O Write me a Hello World in Python."
        expected_output = OutputCommand(Message("Write me a Hello World in Python."))
        self.assertEqual(parse_input(input_str), expected_output)

    def test_update_command(self):
        input_str = "/u fluff"
        expected_output = UpdateCommand()
        self.assertEqual(parse_input(input_str), expected_output)

        input_str = "/U fluff"
        expected_output = UpdateCommand()
        self.assertEqual(parse_input(input_str), expected_output)

    def test_plain_text_command(self):
        input_str = " /p How does continuation passing style work?"
        expected_output = PlainTextCommand(Message("How does continuation passing style work?"))
        self.assertEqual(parse_input(input_str), expected_output)

        input_str = " /P How does recursion work?   "
        expected_output = PlainTextCommand(Message("How does recursion work?"))
        self.assertEqual(parse_input(input_str), expected_output)

    def test_file_selector_command(self):
        input_str = "/fs"
        expected_output = FileSelectorCommand()
        self.assertEqual(parse_input(input_str), expected_output)

        input_str = "/FS"  
        expected_output = FileSelectorCommand()
        self.assertEqual(parse_input(input_str), expected_output)

    def test_message(self):
        input_str = "What are the differences between TypeScript and C#?"
        expected_output = Message("What are the differences between TypeScript and C#?")
        self.assertEqual(parse_input(input_str), expected_output)

        input_str = "   What is the purpose of the 'async' keyword?   "
        expected_output = Message("What is the purpose of the 'async' keyword?")
        self.assertEqual(parse_input(input_str), expected_output)

    def test_model_instruction(self):
        input_str = "@gpt-4o Check that code."
        expected_output = ModelInstruction("gpt-4o", Message("Check that code."))
        self.assertEqual(parse_input(input_str), expected_output)

        input_str = "@GPT-4o Explain the difference between lists and tuples."
        expected_output = ModelInstruction("gpt-4o", Message("Explain the difference between lists and tuples."))
        self.assertEqual(parse_input(input_str), expected_output)

    def test_invalid_model(self):
        input_str = "@copilot Check that code."
        expected_output = Error("Invalid model 'copilot'")
        self.assertEqual(parse_input(input_str), expected_output)

    def test_error_with_invalid_command(self):
        input_str = "/x Invalid command"
        expected_output = Error("Invalid command '/x'")
        self.assertEqual(parse_input(input_str), expected_output)

    def test_error_with_missing_message(self):
        input_str = "@gpt-3.5"
        expected_output = Error("Missing message for model instruction")
        self.assertEqual(parse_input(input_str), expected_output)

if __name__ == '__main__':
    unittest.main()