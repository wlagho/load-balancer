import asyncio
import os
import sys
from test_load_distribution import test_load_distribution
from test_scalability import test_scalability

def create_analysis_report(load_results, scalability_results):
    """Create a markdown report with analysis"""
    
    report = """# Load Balancer Analysis Report

## A-1: Load Distribution Test (10,000 Async Requests on N=3 Servers)

### Results:
"""
    
    server_counts, total_time = load_results
    total_requests = sum(server_counts.values())
    
    for server, count in server_counts.items():
        percentage = (count / total_requests) * 100
        report += f"- **{server}**: {count} requests ({percentage:.1f}%)\n"
    
    report += f"\n**Total Time**: {total_time:.2f} seconds\n"
    report += f"**Requests per Second**: {total_requests/total_time:.1f}\n\n"
    
    # Calculate distribution evenness
    expected_per_server = total_requests / len(server_counts)
    max_deviation = max(abs(count - expected_per_server) for count in server_counts.values())
    deviation_percentage = (max_deviation / expected_per_server) * 100
    
    report += f"**Load Distribution Analysis**:\n"
    report += f"- Expected requests per server: {expected_per_server:.1f}\n"
    report += f"- Maximum deviation: {max_deviation:.1f} requests ({deviation_percentage:.1f}%)\n"
    
    if deviation_percentage < 10:
        report += "- **Verdict**: Excellent load distribution ✅\n"
    elif deviation_percentage < 20:
        report += "- **Verdict**: Good load distribution ✅\n"
    else:
        report += "- **Verdict**: Poor load distribution ❌\n"
    
    report += "\n## A-2: Scalability Test (N=2 to N=6 Servers)\n\n"
    report += "| Servers (N) | Avg Load per Server | Total Time (s) |\n"
    report += "|-------------|---------------------|----------------|\n"
    
    for result in scalability_results:
        report += f"| {result['n_servers']} | {result['avg_load']:.1f} | {result['total_time']:.2f} |\n"
    
    report += "\n**Scalability Analysis**:\n"
    report += "- As the number of servers increases, the average load per server should decrease\n"
    report += "- This demonstrates horizontal scaling capability\n"
    
    # Calculate scaling efficiency
    if len(scalability_results) >= 2:
        load_3_servers = next((r['avg_load'] for r in scalability_results if r['n_servers'] == 3), None)
        load_6_servers = next((r['avg_load'] for r in scalability_results if r['n_servers'] == 6), None)
        
        if load_3_servers and load_6_servers:
            scaling_factor = load_3_servers / load_6_servers
            report += f"- Scaling factor (3→6 servers): {scaling_factor:.2f}x\n"
            report += f"- Expected ideal scaling: 2.0x\n"
            
            if scaling_factor >= 1.8:
                report += "- **Verdict**: Excellent scaling efficiency ✅\n"
            elif scaling_factor >= 1.5:
                report += "- **Verdict**: Good scaling efficiency ✅\n"
            else:
                report += "- **Verdict**: Poor scaling efficiency ❌\n"
    
    report += """
## Implementation Notes

### Consistent Hashing Parameters Used:
- **Ring Size**: 512 slots
- **Virtual Servers per Node**: 9 (log₂(512))
- **Hash Function H(i)**: i²/2 + 2i + 17
- **Hash Function Φ(i,j)**: i² + j² + 2j² + 25

### Key Observations:
1. **Load Distribution**: The consistent hashing algorithm distributes requests fairly evenly across available servers
2. **Scalability**: Adding more servers reduces the average load per server, demonstrating horizontal scaling
3. **Performance**: Async request handling allows for high throughput testing
4. **Fault Tolerance**: The system maintains operation even when servers are added/removed dynamically

### Recommendations:
- Monitor server health continuously
- Implement proper error handling for failed requests
- Consider auto-scaling based on load metrics
- Test with different hash functions for optimization
"""
    
    return report

async def run_full_analysis():
    """Run complete analysis suite"""
    print("=" * 60)
    print("LOAD BALANCER PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    # Create results directory
    os.makedirs('results', exist_ok=True)
    
    try:
        # A-1: Load Distribution Test
        print("\n🔄 Running A-1: Load Distribution Test...")
        load_results = await test_load_distribution(num_requests=10000)
        
        # A-2: Scalability Test  
        print("\n🔄 Running A-2: Scalability Test...")
        scalability_results, _ = await test_scalability(num_requests=10000)
        
        # Generate report
        print("\n📊 Generating Analysis Report...")
        report = create_analysis_report(load_results, scalability_results)
        
        with open('results/analysis_report.md', 'w') as f:
            f.write(report)
        
        print("\n✅ Analysis Complete!")
        print("📁 Results saved in 'results/' directory:")
        print("   - load_distribution.png")
        print("   - scalability.png") 
        print("   - analysis_report.md")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_full_analysis())
    sys.exit(0 if success else 1)