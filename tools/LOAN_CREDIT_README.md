# RISE Loan and Credit Planning System

Comprehensive loan and credit planning system with financing needs assessment, loan product recommendations, and crop-cycle aligned repayment scheduling for informed financial decisions.

## Features

### 1. Financing Needs Assessment
- **Comprehensive evaluation**: Analyzes farmer profile, farm details, and loan purpose
- **Repayment capacity analysis**: Calculates monthly surplus and capacity level
- **Eligibility determination**: Checks age, land ownership, credit score, and repayment capacity
- **Smart recommendations**: Provides loan type, tenure, and amount suggestions
- **Alternative options**: Suggests alternatives when not eligible

### 2. Loan Product Recommendations
- **Multi-lender database**: Banks, NBFCs, and development banks
- **Intelligent matching**: Filters products by amount, purpose, and eligibility
- **Suitability scoring**: Ranks products based on interest rate, fees, and features
- **Comprehensive comparison**: EMI, total interest, and total repayment calculations
- **Product features**: Detailed information on benefits and requirements

### 3. Crop-Cycle Aligned Repayment Schedule
- **Harvest-aligned payments**: Marks harvest months for easier planning
- **Income pattern integration**: Considers expected income by month
- **Payment feasibility analysis**: Identifies challenging months
- **Detailed breakdown**: Principal, interest, and balance for each month
- **Smart recommendations**: Strategies for managing difficult payment periods

### 4. Financial Document Compilation
- **Purpose-specific checklists**: Documents required based on loan type and amount
- **Mandatory vs optional**: Clear indication of required documents
- **Format guidance**: Specific format requirements for each document
- **Financial summary**: Comprehensive applicant and farm financial overview
- **Application process guide**: Step-by-step instructions for loan application

### 5. Loan Affordability Calculator
- **FOIR-based calculation**: 40% Fixed Obligation to Income Ratio
- **Existing loan consideration**: Accounts for current EMI obligations
- **Maximum loan amount**: Calculates affordable loan based on income
- **Debt-to-income ratio**: Comprehensive financial health assessment
- **Status-based recommendations**: Personalized advice based on affordability

## Installation

```bash
# Install required dependencies
pip install boto3 plotly pandas streamlit

# Set up AWS credentials
aws configure

# Set environment variables (optional)
export AWS_REGION=us-east-1
```

## Usage

### Python API

#### 1. Assess Financing Needs

```python
from tools.loan_credit_tools import LoanCreditTools

tools = LoanCreditTools()

farmer_profile = {
    'name': 'Ravi Kumar',
    'age': 35,
    'annual_farm_income': 250000,
    'other_income': 50000,
    'annual_expenses': 180000,
    'credit_score': 680,
    'land_ownership': True
}

farm_details = {
    'farm_size_acres': 5.0,
    'soil_type': 'loamy',
    'crops': ['wheat', 'rice']
}

result = tools.assess_financing_needs(
    farmer_profile=farmer_profile,
    farm_details=farm_details,
    purpose='equipment_purchase'
)

if result['success']:
    print(f"Required Amount: ₹{result['required_amount']:,.0f}")
    print(f"Eligibility: {'ELIGIBLE' if result['eligibility']['eligible'] else 'NOT ELIGIBLE'}")
    print(f"Recommendation: {result['recommendation']['message']}")
```

#### 2. Recommend Loan Products

```python
result = tools.recommend_loan_products(
    required_amount=200000,
    purpose='equipment_purchase',
    farmer_profile={'credit_score': 680},
    location={'state': 'Punjab'},
    repayment_period_months=60
)

if result['success']:
    print(f"Found {result['total_products_found']} products")
    
    for product in result['recommendations']:
        print(f"\n{product['lender_name']} - {product['product_name']}")
        print(f"Interest Rate: {product['interest_rate']}%")
        print(f"Monthly EMI: ₹{product['calculated_emi']:,.0f}")
        print(f"Total Interest: ₹{product['total_interest']:,.0f}")
```

#### 3. Generate Repayment Schedule

```python
crop_cycle = {
    'harvest_months': [6, 12, 18, 24],
    'harvest_income': 100000
}

result = tools.generate_repayment_schedule(
    loan_amount=200000,
    interest_rate=9.5,
    tenure_months=24,
    crop_cycle=crop_cycle
)

if result['success']:
    print(f"Monthly EMI: ₹{result['monthly_emi']:,.0f}")
    print(f"Total Interest: ₹{result['total_interest']:,.0f}")
    print(f"Challenging Months: {result['challenging_months']}")
    
    for month_data in result['schedule']:
        print(f"Month {month_data['month']}: "
              f"EMI ₹{month_data['emi']:,.0f}, "
              f"Balance ₹{month_data['balance']:,.0f}, "
              f"Feasibility: {month_data['payment_feasibility']}")
```

#### 4. Compile Financial Documents

```python
result = tools.compile_financial_documents(
    farmer_profile=farmer_profile,
    farm_details=farm_details,
    loan_purpose='equipment_purchase',
    loan_amount=200000
)

if result['success']:
    print(f"Processing Time: {result['estimated_processing_time']}")
    
    print("\nRequired Documents:")
    for doc in result['required_documents']:
        mandatory = 'MANDATORY' if doc['mandatory'] else 'OPTIONAL'
        print(f"  {mandatory}: {doc['document']}")
        print(f"    Format: {doc['format']}")
```

#### 5. Calculate Loan Affordability

```python
existing_loans = [
    {'emi': 3000, 'type': 'personal_loan'},
    {'emi': 2000, 'type': 'vehicle_loan'}
]

result = tools.calculate_loan_affordability(
    monthly_income=25000,
    monthly_expenses=12000,
    existing_loans=existing_loans,
    interest_rate=9.5,
    tenure_months=60
)

if result['success']:
    print(f"Max Affordable EMI: ₹{result['max_affordable_emi']:,.0f}")
    print(f"Max Loan Amount: ₹{result['max_loan_amount']:,.0f}")
    print(f"Affordability Status: {result['affordability_status'].upper()}")
    print(f"Recommendation: {result['recommendation']}")
```

### Lambda Function

#### Event Structure

```json
{
  "action": "assess_needs",
  "farmer_profile": {
    "name": "Ravi Kumar",
    "age": 35,
    "annual_farm_income": 250000,
    "other_income": 50000,
    "annual_expenses": 180000,
    "credit_score": 680,
    "land_ownership": true
  },
  "farm_details": {
    "farm_size_acres": 5.0,
    "soil_type": "loamy",
    "crops": ["wheat", "rice"]
  },
  "purpose": "equipment_purchase"
}
```

#### Supported Actions

- `assess_needs`: Comprehensive financing needs assessment
- `recommend_products`: Loan product recommendations (requires `required_amount`, `purpose`)
- `generate_schedule`: Repayment schedule generation (requires `loan_amount`, `interest_rate`, `tenure_months`)
- `compile_documents`: Document checklist compilation (requires `loan_purpose`, `loan_amount`)
- `calculate_affordability`: Affordability calculation (requires `monthly_income`, `interest_rate`, `tenure_months`)

### Streamlit UI

```bash
# Run the loan calculator UI
streamlit run ui/loan_calculator.py
```

The UI provides four main tabs:
1. **Financing Needs**: Assess loan requirements and eligibility
2. **Loan Products**: Compare products from multiple lenders
3. **Repayment Schedule**: Generate crop-cycle aligned payment plans
4. **Document Checklist**: Required documents and application guidance

## Data Models

### Financing Needs Assessment Result

```python
{
    'success': True,
    'assessment_id': 'assess_abc123',
    'required_amount': 150000,
    'repayment_capacity': {
        'annual_income': 300000,
        'annual_expenses': 180000,
        'annual_surplus': 120000,
        'monthly_surplus': 10000,
        'capacity_level': 'high',
        'max_monthly_emi': 4000
    },
    'eligibility': {
        'eligible': True,
        'eligibility_factors': [
            {'factor': 'age', 'status': 'eligible', 'detail': 'Age 35 is within range'},
            {'factor': 'land_ownership', 'status': 'eligible', 'detail': 'Owns agricultural land'},
            {'factor': 'repayment_capacity', 'status': 'eligible', 'detail': 'High repayment capacity'},
            {'factor': 'credit_score', 'status': 'eligible', 'detail': 'Good credit score: 680'}
        ],
        'recommended_amount': 150000
    },
    'recommendation': {
        'recommendation_type': 'recommended',
        'loan_type': 'term_loan',
        'recommended_amount': 150000,
        'recommended_tenure_months': 60,
        'estimated_emi': 3240,
        'max_affordable_emi': 4000,
        'message': 'Eligible for term_loan with 60 months tenure',
        'next_steps': [...]
    }
}
```

### Loan Product Recommendation Result

```python
{
    'success': True,
    'required_amount': 200000,
    'purpose': 'equipment_purchase',
    'recommendations': [
        {
            'lender_name': 'State Bank of India',
            'lender_type': 'bank',
            'product_name': 'SBI Agricultural Term Loan',
            'interest_rate': 9.5,
            'default_tenure_months': 60,
            'processing_fee_percent': 1.0,
            'calculated_emi': 4193,
            'total_interest': 51580,
            'total_repayment': 251580,
            'suitability_score': 85,
            'features': [...],
            'eligibility': 'Farmers with land ownership and good credit'
        }
    ],
    'total_products_found': 8
}
```

## Loan Products Database

The system includes comprehensive loan products from:

### Nationalized Banks
- **State Bank of India**: Kisan Credit Card, Agricultural Term Loan
- **Punjab National Bank**: Kisan Credit Card
- **Canara Bank**: Kisan Credit Card
- **Bank of Baroda**: Baroda Kisan Tatkal Scheme
- **HDFC Bank**: Tractor Loan

### NBFCs
- **Mahindra Finance**: Tractor Loan
- **Tata Capital**: Farm Equipment Loan

### Development Banks
- **NABARD**: Refinance Scheme

## Loan Purposes Supported

- **crop_cultivation**: Short-term crop loans (12 months)
- **equipment_purchase**: Medium-term equipment loans (60-84 months)
- **land_improvement**: Long-term infrastructure loans (84 months)
- **irrigation_setup**: Medium-term irrigation loans (60 months)
- **livestock**: Medium-term livestock loans (60 months)
- **storage_facility**: Long-term storage loans (84 months)
- **working_capital**: Short-term working capital (12 months)

## Interest Rates

- **Banks**: 7-10% p.a.
- **NBFCs**: 10-13% p.a.
- **Development Banks**: 6-8% p.a.
- **Government Schemes**: Interest subvention available

## Eligibility Criteria

### Age
- Minimum: 21 years
- Maximum: 65 years

### Land Ownership
- Preferred but not always mandatory
- May require guarantor if no land ownership

### Credit Score
- Excellent: 700+
- Good: 600-699
- Fair: Below 600 (may face challenges)

### Repayment Capacity
- Based on 40% FOIR (Fixed Obligation to Income Ratio)
- Considers existing loan obligations
- Evaluates monthly surplus

## Document Requirements

### Base Documents (All Loans)
1. Identity Proof (Aadhaar, PAN, Voter ID)
2. Address Proof (Aadhaar, Electricity Bill)
3. Land Ownership Documents (7/12 Extract)
4. Bank Statements (Last 6 months)
5. Passport Size Photographs

### Additional Documents
- **Equipment Purchase**: Equipment quotation
- **Large Loans (>₹5 lakh)**: Collateral documents
- **Income Proof**: ITR, Form 16 (if available)

## Repayment Schedule Features

### Crop-Cycle Alignment
- Marks harvest months for easier planning
- Considers expected income from harvests
- Identifies challenging months with low income

### Payment Feasibility
- **High**: Expected income >= EMI
- **Medium**: Some income but < EMI
- **Low**: No expected income

### Recommendations
- Build 3-month EMI buffer
- Consider crop insurance
- Explore interest subvention schemes
- Set up auto-debit for timely payments
- Request moratorium during crop growth

## Integration with Other RISE Tools

### Profitability Calculator
- Uses crop profitability data for income estimation
- Validates loan amount against expected returns
- Provides realistic repayment capacity assessment

### Crop Selection Tools
- Aligns loan purpose with recommended crops
- Considers crop cycle for repayment planning
- Validates equipment needs against crop requirements

### Government Scheme Tools
- Identifies interest subvention schemes
- Recommends subsidy-linked loan products
- Helps maximize government benefits

## Examples

See `examples/loan_credit_example.py` for comprehensive usage examples including:
1. Financing needs assessment
2. Loan product recommendations
3. Crop-cycle aligned repayment schedule
4. Financial document compilation
5. Loan affordability calculation

## Testing

```bash
# Run unit tests
python -m pytest tests/test_loan_credit.py -v

# Run specific test
python -m pytest tests/test_loan_credit.py::TestLoanCreditTools::test_assess_financing_needs_success -v
```

## AWS Resources

### DynamoDB Tables

**RISE-LoanProducts**
- Stores loan product information from banks and NBFCs
- Indexed by lender_name and product_name
- Updated periodically with latest rates

**RISE-LoanApplications**
- Stores loan application tracking data
- Indexed by application_id and farmer_id
- 180-day TTL for completed applications

### Lambda Function

**RISE-LoanCreditPlanner**
- Handles loan planning requests
- Integrates with profitability and crop tools
- Returns comprehensive loan recommendations

## Performance

- **Financing needs assessment**: < 200ms
- **Loan product recommendations**: < 300ms
- **Repayment schedule generation**: < 150ms
- **Document compilation**: < 100ms
- **Affordability calculation**: < 50ms

## Limitations

1. **Loan products**: Database includes major lenders; regional banks may not be covered
2. **Interest rates**: Rates are indicative; actual rates may vary
3. **Eligibility**: Simplified criteria; actual bank criteria may be more complex
4. **Credit score**: Assumes availability; many farmers may not have formal credit history

## Future Enhancements

- [ ] Real-time interest rate updates from bank APIs
- [ ] Integration with credit bureaus for actual credit scores
- [ ] Direct loan application submission to banks
- [ ] Loan tracking and EMI reminder system
- [ ] Integration with digital payment systems
- [ ] Loan restructuring and refinancing options
- [ ] Insurance premium calculations
- [ ] Subsidy claim automation

## Support

For issues, questions, or contributions:
- Check the examples directory for usage patterns
- Review test cases for expected behavior
- Consult the main RISE documentation

## License

Part of the RISE (Rural Innovation and Sustainable Ecosystem) project.
