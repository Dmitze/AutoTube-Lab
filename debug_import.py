import sys
import traceback

sys.path.insert(0, '.')

try:
    from modules.orchestrator import YTAIMBotOrchestrator
    print(f"Successfully imported YTAIMBotOrchestrator: {YTAIMBotOrchestrator}")
except ImportError as e:
    print(f"ImportError with 'from modules.orchestrator import YTAIMBotOrchestrator': {e}")
    traceback.print_exc() # Print full traceback
    try:
        import modules.orchestrator
        print(f"Successfully imported modules.orchestrator module.")
        if hasattr(modules.orchestrator, 'YTAIMBotOrchestrator'):
            print(f"modules.orchestrator.YTAIMBotOrchestrator found: {modules.orchestrator.YTAIMBotOrchestrator}")
        else:
            print(f"modules.orchestrator module has no attribute 'YTAIMBotOrchestrator'. dir(): {dir(modules.orchestrator)}")
    except Exception as e_inner:
        print(f"Error importing modules.orchestrator: {e_inner}")

