from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .parser import extract_text_from_pdf, parse_questions
from .similarity import group_similar_questions
from .models import QuestionGroup, QuestionVariant
import traceback


@api_view(['POST'])
def analyze_papers(request):
    files = request.FILES.getlist('papers')

    if not files:
        return Response(
            {"error": "No PDF files uploaded."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Step 1: Extract questions from all PDFs
    all_questions = []
    for pdf_file in files:
        try:
            print(f"\n=== Processing {pdf_file.name} ===")
            
            text = extract_text_from_pdf(pdf_file)
            print(f"Extracted text length: {len(text)} characters")
            print(f"First 300 chars: {text[:300]}")
            
            questions = parse_questions(text)
            print(f"Questions found: {len(questions)}")
            
            if questions:
                print(f"First question: {questions[0][:150]}")
            
            for q in questions:
                all_questions.append({
                    "text": q,
                    "source": pdf_file.name
                })
                
        except Exception as e:
            print(f"\n!!! ERROR processing {pdf_file.name} !!!")
            print(traceback.format_exc())
            return Response(
                {"error": f"Failed to process {pdf_file.name}: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    print(f"\n=== Total questions extracted from all files: {len(all_questions)} ===\n")

    if not all_questions:
        return Response(
            {"error": "Could not extract questions from uploaded files."},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    # Step 2: Group similar questions using NLP
    try:
        print("Starting similarity grouping...")
        ranked_groups = group_similar_questions(all_questions)
        print(f"Created {len(ranked_groups)} groups")
    except Exception as e:
        print(f"\n!!! ERROR in similarity grouping !!!")
        print(traceback.format_exc())
        return Response(
            {"error": f"Failed during similarity analysis: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Step 3: Save results to MySQL
    try:
        QuestionGroup.objects.all().delete()  # Clear previous results

        saved_groups = []
        for g in ranked_groups:
            group = QuestionGroup.objects.create(
                representative=g["representative"],
                priority=g["priority"],
                count=g["count"]
            )
            variants = []
            for i, variant_text in enumerate(g["variants"]):
                variant = QuestionVariant.objects.create(
                    group=group,
                    text=variant_text,
                    source_file=g["sources"][i]
                )
                variants.append({
                    "text": variant.text,
                    "source": variant.source_file
                })

            saved_groups.append({
                "id": group.id,
                "representative": group.representative,
                "priority": group.priority,
                "count": group.count,
                "variants": variants
            })

        print(f"Saved {len(saved_groups)} groups to database")

    except Exception as e:
        print(f"\n!!! ERROR saving to database !!!")
        print(traceback.format_exc())
        return Response(
            {"error": f"Failed to save results: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Step 4: Return response to React
    return Response({
        "total_questions_extracted": len(all_questions),
        "total_groups": len(saved_groups),
        "papers_analyzed": [f.name for f in files],
        "ranked_questions": saved_groups
    })


@api_view(['GET'])
def health(request):
    return Response({"status": "ok"})