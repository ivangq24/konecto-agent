"""
Part Number Search Tool Module

This module provides a LangChain tool for performing exact searches by Base Part Number
in SQLite. The tool enables the AI agent to quickly retrieve detailed specifications
for specific actuators when users provide exact part numbers.

The tool:
- Accepts Base Part Number as input (exact or partial match)
- Searches SQLite database for matching actuators
- Returns formatted results with complete specifications
- Handles errors gracefully and provides informative messages

Use Cases:
- User provides exact Base Part Number (e.g., "763A00-11330C00/A")
- User asks about a specific actuator model
- User wants detailed specifications for a known part number
- User provides partial part number (tool performs partial matching)
"""

from typing import TYPE_CHECKING
from langchain_core.tools import tool
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.services.data_service import DataService


class PartNumberSearchInput(BaseModel):
    """
    Input schema for part number search tool.
    
    Defines the parameters required for searching actuators by Base Part Number
    in the SQLite database.
    
    Attributes:
        part_number: The Base Part Number to search for (exact or partial match)
    """
    part_number: str = Field(
        description="The Base Part Number to search for (e.g., '763A00-11330C00/A')"
    )


def create_part_number_search_tool(data_service: "DataService"):
    """
    Create a part number search tool with data_service injected.
    
    This factory function creates a LangChain tool that performs exact searches
    by Base Part Number in SQLite. The tool is configured with the provided
    DataService instance which handles the actual database queries.
    
    Args:
        data_service: DataService instance for accessing SQLite database
        
    Returns:
        LangChain tool function configured for part number search
    """
    
    @tool("search_by_part_number", args_schema=PartNumberSearchInput)
    def search_by_part_number(part_number: str) -> str:
        """
        Search for an actuator by its exact Base Part Number.
        
        This tool performs exact and partial match searches in SQLite for actuators
        matching the provided Base Part Number. It returns complete specifications
        including voltage/power configuration, torque, speed, duty cycle, and all
        other technical parameters.
        
        Use this tool when:
        - User provides a specific Base Part Number
        - User asks about a specific actuator model number
        - User wants detailed specifications for a known part number
        
        Args:
            part_number: The Base Part Number to search for (exact or partial match)
            
        Returns:
            A formatted string with the actuator specifications if found.
            The output includes:
            - Base Part Number
            - Voltage/Power (Context Type)
            - Priority specifications (torque, speed, duty cycle, etc.)
            - All other available technical parameters
            
            Returns an error message if no results are found.
            
        Raises:
            No explicit exceptions, but returns error messages as strings if:
            - Data service is not available
            - No results are found
            - Database query fails
        """
        if not data_service:
            return "Error: Data service not available"
        
        try:
            results = data_service.search_by_part_number(part_number)
            
            if not results:
                return f"No actuator found with Base Part Number: {part_number}"
        
            # Format the results
            formatted_results = []
            for result in results:
                # Get the most relevant fields
                base_part = result.get("base_part_number") or result.get("identifier", "N/A")
                context_type = result.get("context_type", "N/A")
                source_table = result.get("source_table", "N/A")
                
                # Build a readable description - Always include context_type prominently
                description = f"Base Part Number: {base_part}\n"
                if context_type and context_type != "N/A":
                    description += f"Voltage/Power: {context_type}\n"
                description += "\nSpecifications:\n"
                
                # Priority fields to show first (if they exist)
                priority_fields = [
                    ("output_torque_nm", "Output Torque (Nm)"),
                    ("on_off_output_torque_nm", "On/Off Output Torque (Nm)"),
                    ("modulating_output_torque_nm", "Modulating Output Torque (Nm)"),
                    ("duty_cycle_54pct", "Duty Cycle 54%"),
                    ("on_off_duty_cycle_54pct", "On/Off Duty Cycle 54%"),
                    ("modulating_duty_cycle_54pct", "Modulating Duty Cycle 54%"),
                    ("motor_power_watts", "Motor Power (Watts)"),
                    ("operating_speed_sec_60_hz", "Operating Speed 60Hz (sec)"),
                    ("operating_speed_sec_50_hz", "Operating Speed 50Hz (sec)"),
                    ("cycles_per_hour_cycles", "Cycles per Hour"),
                    ("starts_per_hour_starts", "Starts per Hour"),
                ]
                
                # Show priority fields first
                shown_fields = set()
                for field_key, field_name in priority_fields:
                    if field_key in result and result[field_key] is not None:
                        value = result[field_key]
                        if value != "" and str(value).lower() != "nan":
                            description += f"- {field_name}: {value}\n"
                            shown_fields.add(field_key)
                
                # Show other numeric/important fields that weren't in priority list
                for key, value in result.items():
                    # Skip already shown fields and metadata fields
                    if key in shown_fields or key in ["base_part_number", "identifier", "context_type", "source_table"]:
                        continue
                    
                    # Show numeric values or non-empty strings
                    if value is not None and value != "" and str(value).lower() != "nan":
                        # Format field name for display
                        display_name = key.replace("_", " ").title()
                        description += f"- {display_name}: {value}\n"
                
                formatted_results.append(description.strip())
            
            return "\n\n---\n\n".join(formatted_results)
            
        except Exception as e:
            return f"Error performing part number search: {str(e)}"
    
    return search_by_part_number

