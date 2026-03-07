The goal for this working session to to plan out the future of annotated training data.

I will take a product-management focused approach.

## Goals

Efficiently create accurate training data for training machine learning models.

## Definition

**Job** - The unit of work that an annotator submits. There are smaller units of work, but all of those units of work are treated as "in progress" until a job is completed.

**Annotations Task** Has jobs, a task spec, and a business problem that is trying to be solved.  
- Previously, annotations tasks were conceptuallized to assign the same fields to be annotated for each document. This new requirement is to be able to assign different fields to be anonotated for each document.

**Operations Task** An action that an AI agent or annotations manager performs.  
 *The work Task could be applied to both.*

## **Problems**

1. Calculating annotators velocity and accuracy on any given job is hard.  
2. Calculating annotators velocity and accuracy across jobs in the same task is hard.  
3. Calculating annotators velocity across different tasks is hard  
4. Annotators are not rewarded for accuracy  
5. When a mistake is found in data, we don't know which annotator made the mistake.  
6. Annotation speed is limited by a single reviewer, Irina, who "Accepts" each job  
7. Annotators must too much. They may learn about how to process a Money Order, and only process a few of them.  
8. Creating training tasks is hard.  
9. An annotator's task is often to review data. It's a problem because, if data is 99% accurate, the annotator is as likely as not to change and correct value to a positive value.  
10. Comparing the accuracy of an annotator that is reviewing data that is 99% correct is incomparable to an annotators that is reviewing data that is 90% correct.

## **Insights**
0. Our machine learning model are between 90 and 99.9% accurate. We're nearly always cleaning data, rather than creating data from scratch.
1. The existing platform, CVAT, isn't meeting our labeling needs  
2. We're not willing to pay 100k a year for a better platform  
3. AI agents allow us to rapidly create software  
4. Creating a system, on top of CVAT, that meets our needs will required 10x more work than building a new system.  
5. Building a new system would not mean "building it from scratch". We will copy code directly from CVAT, Label Studio. Likely, we'll copy LabelStudio.
6. I, Owen, never really worked with the other tools. So, I'm re-inventing the wheel because I don't know what premium features exist. On the other hand, I'm not constrained by the their thinking.  
7. People that create great film, writing, and software, usually start by looking at the great work of others and copying what they lie.  
8. I can do research in parallel.  
   1. I can research the features of the other platforms while I work on other things  
9. I could create an open-source HTML page or application for labeling data. If I do that I can do it from my other laptop.  
10. Managers perform the same 10 or 20 data labeling tasks over and over again. The way these tasks are organized currently, the manage needs to load a lot of context into their head and also perform an lot of repetitive steps.  
11. The existing platform cannot be operated by an agent.
    1. Information needed to operate the system isn't stored in files that an agent can read  
    2. Because common workflows are not organized and workflows are not codified, the total context needed for the agent to understand the system exceeds the agents working context  
    3. Loading the context, from the existing system, into the agent would wake 10x more time than doing the work directly.  
12. AI agent workflows require "review" steps.  
    1. If we were to enable AI agents to create tasks and jobs, we would need to design a system that allows a manager to "review" data prior to assigning it to humans.  
    2. AI agents make mistakes. Humans do to. It's a requirement that mistakes in creating task can be easily corrected. So, adding or removing documents from a task, updating fields in a task, etc., should be handled easily  
13. Jira is awful, dispiriting to work with.  
14. NinjaAPI and tiered architecture make things manageable
15. The system must support working with third-party data annotation companies.
  16. The problem we faced with the previous annotations company is that they consistently sent us low quality work. We ought to have fired them tout de suite. 
17. Annotations tasks tend to be:
  - Measuring the accuracy of an existing data set, which is old or provided by a third party
  - Creating a new data set
  - Adding new documents to a data set
  - Adding new fields to a data set
  - Updating a field in a data set, because the definition changed
  - Updating a field in a data set, because it is known to be dirty
  - Clean an entire dataset, because it is low quality

  A question is, what is the conceptual model for accepting annotation from a third party? Is the submission treated like an other "Job"? 
  
  I do like the concept of a job NOT being reviewed until it is "Complete" (different than "Accepted").
  
  It would be great to work through the conceptual model of how one annotator reviews a second annotators work. I haven't thought through this before. 

##### **List of task that humans an AI perform**
Most performed
1. Identify documents that need to be annotated  
2. Identify possibly incorrectly annotated fields.
2. Document the reason for annotations  
3. Specify the meaning of data. i.e., create the task spec.  
4. Assign work to annatators.  
5. Pay annotators for doing high quality work.  
6. Measure the accuracy of annotators.  
7. Measure the velocity of annotators.
8. Measure overall performance of annotator across task.
9. Create golden and honeypot data.
10. Annotator annotates a document
11. Annotator navigates to the work that is assigned to him
12. Annotators asks questions about a document
13. Answers questions about a document
14. Pushes document to the ML training server
15. Reports volume of documents annotate
16. Plans which annotations will be done in a week, and how long it will take
17. Update incorrect golden data happens all the time and needs to be easy
18. The "Accuracy" of an annotation shouldn't be based on the accuarcy of the final documents. It should be based on the % of errors corrected. But...this isn't quite fair because, spotting 1 error in 10 might be easier than spotting 1 error in 100.

## Requirement: Use AI to find bad annotations
- Our machine learning models are pretty accurate. 

## Ramble 
It might be interesting to have a confidence score for fields.

## Requirements

##### Design
1. The system should be as simple as possible. Complexity, when necessary, should remain isolated.  
2. The system should be operable by AI agents and humans.  
3. The system should efficiently manage the context of AI agents and humans. When either a human or an AI agent is performing a operations task, documentation, stored in a markdown file in the code base but human readable at a webpage, should contain the information and agent or human needs. AI agent calls appropriate DjangoNinja endpoints. UI for humans should limit required context and link out to documentation.
4. The system should be understandable at multiple levels. 
5. The system must be very fast to load and work with. Both annotators and managers should love working with the system
6. Querying the data in the system must be fast. We have **very small** data so we don't need to overengineer this.

## Measure accuracy
1. Every data has the possiblity of being wrong. We want t
2. Measuring the accuracy of the 'golden data' is an open proble.
  3. Because we will give annotators the ability to "challenge" golden data, and also because the managers review their mistakes of annotators, most Golden Data problems should get caught. So

## Workflow
1. Articulate the business problem being solved. 
  - For humans, sometimes this is articulated in Jira ticket, or a conversation.
  - For an AI agent, this might articulated through a conversation with the manager in, for example, Claude Code or Cursor.
2. Decide what (document, fields) need to be updated.
  - A given "Annotations Task" might have fields being annotated on each document. For example, 
  7. The system must support partially annotating a document.
  - A task might consist of some documents being annotated for one field, and some documents being annotated with a separate field




## Design
Design of the system starts with re-desigining 

1. Start agents researching the existing platforms

# Problem / cosideration
- I have been thinking in terms of how the data needs to be stored, to efficiently annotate and clean.
- However, my model requires stitching together field-level data into data that can be trained on.


-
The most important consideration is how to support multiple annotators annotating the same document, without bottlenecking the manager.
I lean toward having an workflow similar to what we used for (amount,amount_text,date) tool. Specifically:
- manager creates golden data
- job is created with mix of "best pre-annotation" and honeypot data
- first annotator completes the job
- second annotator reviews first annotators work, but with errors injected.
 

## Tasks
1. Finish writing up requirements
2. Write up models
3. Write up decision - what is not yet decided
4. Write up workflows
  5. Write up inputs and outputs for each function / service
6.
